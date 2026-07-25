function z = zscore(x)
% Standardise columns to mean 0, standard deviation 1 (ddof = 1). Shim for
% fixture generation only: upstream's LPmodel calls zscore, which lives in the
% Statistics and Machine Learning Toolbox. Matches its default behaviour.
z = (x - mean(x)) ./ std(x, 0);
end
