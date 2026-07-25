% Generate reference fixtures from the MATLAB VAR Toolbox 4.0 for pyvartoolbox.
% Writes plain CSVs into OUTDIR; a Python step converts them to .npz.
% Point estimates only (VARopt.inference = 0) so the fixtures are exactly
% reproducible and carry no RNG dependence.

clear all; close all; clc
warning off all

TB     = fullfile(fileparts(mfilename('fullpath')), 'VAR-Toolbox');
OUTDIR = fullfile(fileparts(mfilename('fullpath')), 'fixtures');
addpath(genpath(TB));
if ~exist(OUTDIR, 'dir'); mkdir(OUTDIR); end

cases = struct( ...
    'name',   {'sw2001',                          'bq1989'}, ...
    'file',   {'Replic/SW2001/SW2001_Data.xlsx',  'Replic/BQ1989/BQ1989_Data.xlsx'}, ...
    'nlags',  {4,                                 8}, ...
    'ident',  {'short',                           'long'}, ...
    'nsteps', {24,                                40});

for c = 1:numel(cases)
    cs = cases(c);
    raw  = readcell(fullfile(TB, cs.file), 'Sheet', 'Sheet1');
    X    = cellfun(@double, raw(3:end, 2:end));

    VARopt           = VARoption;
    VARopt.ident     = cs.ident;
    VARopt.nsteps    = cs.nsteps;
    VARopt.inference = 0;      % point estimates only
    VARopt.impact    = 0;      % one-standard-deviation shocks
    VARopt.recurs    = 'wold';

    VAR = VARmodel(X, cs.nlags, 1, VARopt);

    p = @(suffix) fullfile(OUTDIR, [cs.name '_' suffix '.csv']);
    dump(X, p('data'));
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

    fprintf('%s: nobs=%d nvar=%d IR=[%d %d %d] VD=[%d %d %d]\n', ...
            cs.name, size(X,1), size(X,2), ns, nv, nsh, vs, vv, vsh);
end

disp('done');

function dump(M, fname)
% Write a numeric matrix as CSV at full float64 precision (%.17g).
fid = fopen(fname, 'w');
fmt = [repmat('%.17g,', 1, size(M,2)-1) '%.17g\n'];
fprintf(fid, fmt, M.');
fclose(fid);
end
