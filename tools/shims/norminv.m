function x = norminv(p, mu, sigma)
% Inverse normal CDF. Shim for fixture generation only: upstream's LPmodel
% calls norminv, which lives in the Statistics and Machine Learning Toolbox.
% This is the exact identity norminv(p) = mu + sigma*sqrt(2)*erfinv(2p-1),
% using erfinv from base MATLAB, so the fixture is unaffected.
if nargin < 2; mu = 0; end
if nargin < 3; sigma = 1; end
x = mu + sigma .* sqrt(2) .* erfinv(2*p - 1);
end
