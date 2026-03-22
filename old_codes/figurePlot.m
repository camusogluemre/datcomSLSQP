data_new = [
-10.0    0.131   -1.397    1.7224  -1.398   -0.114   -1.232    1.415E-01   -1.930E-01;
 -8.0    0.089   -1.114    1.3305  -1.116   -0.067   -1.192    1.401E-01   -1.912E-01;
 -6.0    0.057   -0.836    0.9577  -0.838   -0.031   -1.143    1.364E-01   -1.802E-01;
 -4.0    0.036   -0.569    0.6097  -0.570   -0.004   -1.069    1.311E-01   -1.681E-01;
 -2.0    0.027   -0.312    0.2854  -0.313    0.016   -0.913    1.267E-01   -1.594E-01;
  0.0    0.028   -0.062   -0.0279  -0.062    0.028    0.450    1.235E-01   -1.521E-01;
  2.0    0.029    0.182   -0.3231   0.183    0.022   -1.766    1.238E-01   -1.494E-01;
  4.0    0.040    0.433   -0.6257   0.435    0.009   -1.438    1.285E-01   -1.561E-01;
  6.0    0.062    0.696   -0.9476   0.699   -0.011   -1.356    1.337E-01   -1.660E-01;
  8.0    0.094    0.968   -1.2896   0.972   -0.041   -1.327    1.382E-01   -1.765E-01;
 10.0    0.137    1.249   -1.6534   1.254   -0.082   -1.319    1.409E-01   -1.861E-01;
 12.0    0.186    1.532   -2.0339   1.537   -0.136   -1.323    1.406E-01   -1.922E-01;
 14.0    0.236    1.811   -2.4221   1.814   -0.209   -1.335    1.339E-01   -1.911E-01;
 16.0    0.299    2.067   -2.7981   2.070   -0.283   -1.352    1.228E-01   -1.849E-01;
 18.0    0.360    2.303   -3.1616   2.301   -0.369   -1.374    1.124E-01   -1.786E-01;


 ];

data_org = [
-10.0    0.100   -1.914    1.4073  -1.903   -0.234   -0.740    1.988E-01   -1.569E-01;
 -8.0    0.070   -1.524    1.0841  -1.519   -0.142   -0.714    1.927E-01   -1.592E-01;
 -6.0    0.051   -1.144    0.7704  -1.143   -0.069   -0.674    1.873E-01   -1.512E-01;
 -4.0    0.037   -0.775    0.4792  -0.776   -0.017   -0.618    1.809E-01   -1.421E-01;
 -2.0    0.031   -0.420    0.2021  -0.421    0.016   -0.480    1.733E-01   -1.354E-01;
  0.0    0.033   -0.082   -0.0623  -0.082    0.033    0.763    1.666E-01   -1.293E-01;
  2.0    0.035    0.246   -0.3153   0.248    0.026   -1.274    1.669E-01   -1.302E-01;
  4.0    0.045    0.586   -0.5831   0.588    0.004   -0.992    1.738E-01   -1.401E-01;
  6.0    0.062    0.942   -0.8759   0.943   -0.037   -0.929    1.818E-01   -1.537E-01;
  8.0    0.083    1.313   -1.1977   1.312   -0.100   -0.913    1.895E-01   -1.679E-01;
 10.0    0.115    1.700   -1.5474   1.694   -0.182   -0.914    1.950E-01   -1.783E-01;
 12.0    0.161    2.093   -1.9110   2.081   -0.278   -0.918    1.930E-01   -1.874E-01;
 14.0    0.210    2.472   -2.2970   2.449   -0.394   -0.938    1.762E-01   -1.872E-01;
 16.0    0.264    2.798   -2.6598   2.762   -0.517   -0.963    1.588E-01   -1.827E-01;
 18.0    0.330    3.107   -3.0279   3.056   -0.646   -0.991    1.499E-01   -1.854E-01;

];

% === plot_aero_results.m ===
% This script plots aerodynamic coefficients versus angle of attack (alpha)
% Example usage for visualizing DATCOM output

% ---------------------------
% 1. Input: Replace these with your actual DATCOM-derived data
alpha = data_org(:,1);         % angle of attack in degrees
CL = data_org(:,3);     % lift coefficient
CD = data_org(:,2); % drag coefficient
CM = data_org(:,4); % pitching moment coefficient

CL_new = data_new(:,3);     % lift coefficient
CD_new = data_new(:,2); % drag coefficient
CM_new = data_new(:,4); % pitching moment coefficient

% ---------------------------

%% First Figure: CL vs Alpha and CD vs Alpha
figure('Name','Aerodynamic Coefficients 1', 'NumberTitle','off', ...
       'Position', [100, 100, 1200, 500]); % [left, bottom, width, height]
tiledlayout(1,2, 'Padding', 'compact', 'TileSpacing', 'compact');

% 1. CL vs Alpha
nexttile;
plot(alpha, CL, 'b-o', 'LineWidth', 2, 'DisplayName','Baseline CL'); hold on;
plot(alpha, CL_new, 'r-o', 'LineWidth', 2, 'DisplayName','Optimized CL');
yline(0, 'k--', 'LineWidth', 1, 'HandleVisibility','off');
xline(0, 'k--', 'LineWidth', 1, 'HandleVisibility','off');
xlabel('\alpha (deg)', 'FontWeight', 'bold');
ylabel('C_L', 'FontWeight', 'bold');
title('Lift Coefficient vs Angle of Attack');
legend('Location','best'); grid on;
L1 = legend('Location','northwest');  % 'best' yerine sabit sol-üst
L1.Title.String = 'Mach = 0.3';
L1.Title.FontWeight = 'normal';

% 2. CD vs Alpha
nexttile;
plot(alpha, CD, 'b-s', 'LineWidth', 2, 'DisplayName','Baseline CD'); hold on;
plot(alpha, CD_new, 'r-s', 'LineWidth', 2, 'DisplayName','Optimized CD');
yline(0, 'k--', 'LineWidth', 1, 'HandleVisibility','off');
xline(0, 'k--', 'LineWidth', 1, 'HandleVisibility','off');
xlabel('\alpha (deg)', 'FontWeight','bold');
ylabel('C_D', 'FontWeight','bold');
title('Drag Coefficient vs Angle of Attack');
legend('Location','best'); grid on;
L2 = legend('Location','northwest');  % 'best' yerine sabit sol-üst
L2.Title.String = 'Mach = 0.3';
L2.Title.FontWeight = 'normal';
exportgraphics(gcf, 'CL_CD_vs_alpha_combined.png', 'Resolution', 300);

%% Second Figure: CM vs Alpha and CL/CD vs Alpha
figure('Name','Aerodynamic Coefficients 2', 'NumberTitle','off', ...
       'Position', [100, 100, 1200, 500]);
tiledlayout(1,2, 'Padding', 'compact', 'TileSpacing', 'compact');

% 3. CM vs Alpha
nexttile;
plot(alpha, CM, 'b-^', 'LineWidth', 2, 'DisplayName','Baseline CM'); hold on;
plot(alpha, CM_new, 'r-^', 'LineWidth', 2, 'DisplayName','Optimized CM');
yline(0, 'k--', 'LineWidth', 1, 'HandleVisibility','off');
xline(0, 'k--', 'LineWidth', 1, 'HandleVisibility','off');
xlabel('\alpha (deg)', 'FontWeight','bold');
ylabel('C_M', 'FontWeight','bold');
title('Moment Coefficient vs Angle of Attack');
legend('Location','best'); grid on;
L3 = legend('Location','northwest');  % 'best' yerine sabit sol-üst
L3.Title.String = 'Mach = 0.3';
L3.Title.FontWeight = 'normal';

% 4. CL/CD vs Alpha
eff_baseline = CL ./ CD;
eff_opt = CL_new ./ CD_new;
nexttile;
plot(alpha, eff_baseline, 'b-o', 'LineWidth', 2, 'DisplayName','Baseline'); hold on;
plot(alpha, eff_opt, 'r-o', 'LineWidth', 2, 'DisplayName','Optimized');
yline(0, 'k--', 'LineWidth', 1, 'HandleVisibility','off');
xline(0, 'k--', 'LineWidth', 1, 'HandleVisibility','off');
xlabel('\alpha (deg)', 'FontWeight','bold');
ylabel('C_L / C_D', 'FontWeight','bold');
title('Lift-to-Drag Ratio vs Angle of Attack');
legend('Location','best'); grid on;
L4 = legend('Location','northwest');  % 'best' yerine sabit sol-üst
L4.Title.String = 'Mach = 0.3';
L4.Title.FontWeight = 'normal';

exportgraphics(gcf, 'CM_CLCD_vs_alpha_combined.png', 'Resolution', 300);



%% 5. dCM/dAlpha vs Alpha
dCM_base = gradient(CM, alpha);
dCM_opt = gradient(CM_new, alpha);
figure('Name','dCM/dAlpha vs Alpha','NumberTitle','off');
plot(alpha, dCM_base, 'b--o', 'LineWidth', 2, 'DisplayName','Baseline'); hold on;
plot(alpha, dCM_opt, 'r--o', 'LineWidth', 2, 'DisplayName','Optimized');
yline(0, 'k--', 'LineWidth', 1, 'HandleVisibility','off');
xline(0, 'k--', 'LineWidth', 1, 'HandleVisibility','off');
xlabel('\alpha (deg)', 'FontWeight','bold');
ylabel('dC_M / d\alpha', 'FontWeight','bold');
title('Pitching Moment Slope vs Angle of Attack');
legend('Location','best');
L5 = legend('Location','northwest');  % 'best' yerine sabit sol-üst
L5.Title.String = 'Mach = 0.3';
L5.Title.FontWeight = 'normal';
grid on;
exportgraphics(gcf, 'dCM_dAlpha_vs_alpha.png', 'Resolution', 300);