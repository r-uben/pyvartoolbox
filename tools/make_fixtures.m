% Generate reference fixtures from the MATLAB VAR Toolbox 4.0 for pyvartoolbox.
% Writes plain CSVs into OUTDIR; a Python step converts them to .npz.
% Point estimates only (VARopt.inference = 0) so the fixtures are exactly
% reproducible and carry no RNG dependence.

clear all; close all; clc
warning off all

TB     = fullfile(fileparts(mfilename('fullpath')), 'VAR-Toolbox');
OUTDIR = fullfile(fileparts(mfilename('fullpath')), 'fixtures');
addpath(genpath(TB));
addpath(fullfile(fileparts(mfilename('fullpath')), 'shims'));  % see tools/shims/README.md
if ~exist(OUTDIR, 'dir'); mkdir(OUTDIR); end

% 'vars' selects endogenous columns by mnemonic ({} = all columns, in file
% order). 'ivvars' selects instrument columns for ident='iv' ({} = none).
cases = struct( ...
    'name',   {'sw2001',                          'bq1989',                          'gk2015'}, ...
    'file',   {'Replic/SW2001/SW2001_Data.xlsx',  'Replic/BQ1989/BQ1989_Data.xlsx',  'Replic/GK2015/GK2015_Data.xlsx'}, ...
    'nlags',  {4,                                 8,                                 12}, ...
    'ident',  {'short',                           'long',                            'iv'}, ...
    'nsteps', {24,                                40,                                48}, ...
    'vars',   {{},                                {},                                {'gs1','logcpi','logip','ebp'}}, ...
    'ivvars', {{},                                {},                                {'ff4_tc'}});

for c = 1:numel(cases)
    cs = cases(c);
    raw  = readcell(fullfile(TB, cs.file), 'Sheet', 'Sheet1');
    mnem = raw(2, 2:end);
    full = cellfun(@double, raw(3:end, 2:end));

    if isempty(cs.vars)
        X = full;
    else
        X = zeros(size(full,1), numel(cs.vars));
        for ii = 1:numel(cs.vars)
            X(:,ii) = full(:, strcmp(mnem, cs.vars{ii}));
        end
    end

    VARopt           = VARoption;
    VARopt.ident     = cs.ident;
    VARopt.nsteps    = cs.nsteps;
    VARopt.inference = 0;      % point estimates only
    VARopt.impact    = 0;      % one-standard-deviation shocks
    VARopt.recurs    = 'wold';

    if ~isempty(cs.ivvars)
        IV = zeros(size(full,1), numel(cs.ivvars));
        for ii = 1:numel(cs.ivvars)
            IV(:,ii) = full(:, strcmp(mnem, cs.ivvars{ii}));
        end
        VARopt.IV = IV;
    end

    VAR = VARmodel(X, cs.nlags, 1, VARopt);

    p = @(suffix) fullfile(OUTDIR, [cs.name '_' suffix '.csv']);
    dump(X, p('data'));
    if ~isempty(cs.ivvars); dump(VARopt.IV, p('iv')); end
    dump(VAR.sigma, p('sigma'));
    dump(VAR.B, p('B'));
    dump(VAR.resid, p('resid'));
    dump(VAR.F, p('F'));

    % IR and VD are 3-D (nsteps x nvar x nshock); flatten to 2-D by stacking
    % shocks vertically, and record the shape so numpy can rebuild them.
    [ns, nv, nsh] = size(VAR.IR);
    dump(reshape(VAR.IR, ns, nv * nsh), p('IR'));
    dump([ns nv nsh], p('IRshape'));

    [vs, vv, vsh] = size(VAR.VD);
    dump(reshape(VAR.VD, vs, vv * vsh), p('VD'));
    dump([vs vv vsh], p('VDshape'));

    % Historical decomposition. compute_HD needs an invertible B, so use the
    % internal completion rather than the zeroed VAR.B stored for partial schemes.
    [Bfull, ~] = recover_B(VAR, VARopt);
    HD = compute_HD(VAR, Bfull);
    [hs, hv, hsh] = size(HD.shock);
    dump(reshape(HD.shock, hs, hv * hsh), p('HDshock'));
    dump([hs hv hsh], p('HDshockshape'));
    dump(HD.init,  p('HDinit'));
    dump(HD.const, p('HDconst'));
    dump(HD.endo,  p('HDendo'));

    fprintf('%s: nobs=%d nvar=%d IR=[%d %d %d] VD=[%d %d %d]\n', ...
            cs.name, size(X,1), size(X,2), ns, nv, nsh, vs, vv, vsh);
end

%% LOCAL PROJECTIONS — Jorda and Taylor (2025), OLS branch
% Separate from the VAR loop because LPmodel has a different call signature.
% Mirrors GO_JT2025.m section 2 exactly: 1985q1-2007q4, lcpi scaled to percent,
% long-difference LHS, unit shock.
raw_lp = readcell(fullfile(TB, 'Replic/JT2025/JT2025_Data.xlsx'), 'Sheet', 'Ex5');
mn_lp  = raw_lp(2, 2:end);
dts    = raw_lp(3:end, 1);
d_lp   = cellfun(@double, raw_lp(3:end, 2:end));

i0 = find(strcmp(dts, '1985q1'));
i1 = find(strcmp(dts, '2007q4'));
col = @(name) d_lp(i0:i1, strcmp(mn_lp, name));

ENDO  = 100 * col('lcpi');
TREAT = col('rr_shock');
CTRL  = [col('dlrgdp') col('dlcpi') col('dstir')];

LPopt          = LPoption;
LPopt.nsteps   = 18;
LPopt.IV       = [];
LPopt.longdiff = 1;
LPopt.impact   = 1;
LPopt.pctg     = 95;
LP = LPmodel(ENDO, TREAT, CTRL, 4, 1, LPopt);

q = @(suffix) fullfile(OUTDIR, ['jt2025_' suffix '.csv']);
dump([ENDO TREAT CTRL], q('data'));
dump(LP.IR,  q('IR'));
dump(LP.INF, q('INF'));
dump(LP.SUP, q('SUP'));
nw = zeros(LPopt.nsteps, 1);
for hh = 1:LPopt.nsteps
    nw(hh) = LP.(['h' num2str(hh)]).bstd_NW(1);
end
dump(nw, q('seNW'));
fprintf('jt2025: nobs=%d H=%d\n', size(ENDO,1), LPopt.nsteps);

%% LP-IV — Jorda and Taylor (2025) section 3, unemployment on FFR
% Mirrors GO_JT2025.m: 1985m1-2000m1, RRCG shock as external instrument.
raw_iv = readcell(fullfile(TB, 'Replic/JT2025/JT2025_Data.xlsx'), 'Sheet', 'Ex6');
mn_iv  = raw_iv(2, 2:end);
dts_iv = raw_iv(3:end, 1);
d_iv   = cellfun(@double, raw_iv(3:end, 2:end));

j0 = find(strcmp(dts_iv, '1985m1'));
j1 = find(strcmp(dts_iv, '2000m1'));
civ = @(name) d_iv(j0:j1, strcmp(mn_iv, name));

ENDO_IV  = civ('urate');
TREAT_IV = civ('ffr');
CTRL_IV  = [civ('urate') civ('infl') civ('ffr')];
INSTR    = civ('RRCGShock');

LPo          = LPoption;
LPo.nsteps   = 49;
LPo.longdiff = 1;
LPo.impact   = 1;
LPo.pctg     = 95;
LPo.IV       = INSTR;
LPo.nlag_iv  = 6;
LPIV = LPmodel(ENDO_IV, TREAT_IV, CTRL_IV, 6, 1, LPo);

r = @(suffix) fullfile(OUTDIR, ['jt2025iv_' suffix '.csv']);
dump([ENDO_IV TREAT_IV CTRL_IV], r('data'));
dump(INSTR,     r('iv'));
dump(LPIV.IR,   r('IR'));
dump(LPIV.INF,  r('INF'));
dump(LPIV.SUP,  r('SUP'));
se_iv = zeros(LPo.nsteps,1); fs = zeros(LPo.nsteps,1);
for hh = 1:LPo.nsteps
    se_iv(hh) = LPIV.(['h' num2str(hh)]).se_iv;
    fs(hh)    = LPIV.(['h' num2str(hh)]).Fstat_fs;
end
dump(se_iv, r('se'));
dump(fs,    r('Fstat'));
fprintf('jt2025iv: nobs=%d H=%d\n', size(ENDO_IV,1), LPo.nsteps);

disp('done');

function dump(M, fname)
% Write a numeric matrix as CSV at full float64 precision (%.17g).
fid = fopen(fname, 'w');
fmt = [repmat('%.17g,', 1, size(M,2)-1) '%.17g\n'];
fprintf(fid, fmt, M.');
fclose(fid);
end
