%clc;
clear all;
%close all;

%— PARAMETERS —%
c0        = 299792458;      % speed of light (m/s)
f         = 3e9;            % 3 GHz
obsCount  = 360;            % one observer per degree
radius    = 10;             % 10 m circle around the target

unvName   = 'dihedral.unv';  % your mesh in UNV format
rbaName   = 'dihedra.rba';  % output from MakeRBA

%— STEP 1: GENERATE RBA FROM UNV —%
RaytrAMP.MakeRBA( unvName, rbaName );

%— BUILD OBSERVER LIST —%
azDeg = 0:obsCount-1;                 % 0°–359°
azRad = deg2rad(azDeg);

obsX = radius * cos(azRad);
obsY = radius * sin(azRad);
obsZ = zeros(size(azRad));            % θ = 0°, side view

% vertical polarization
polX = zeros(size(azRad));
polY = zeros(size(azRad));
polZ = ones (size(azRad));

% same freq + density
freq      = repmat(f,       obsCount, 1);
rayPerLam = repmat(10,      obsCount, 1);

%— WRITE .obs, RUN & LOAD —%
RaytrAMP.GenerateObsFile( ...
    'obs360_3GHz_side.obs', ...
    obsCount, ...
    obsX', obsY', obsZ', ...
    polX', polY', polZ', ...
    freq, rayPerLam ...
);
RaytrAMP.MonoRCS( ...
    rbaName, ...
    'obs360_3GHz_side.obs', ...
    'rcs360_3GHz_side.rcs' ...
);
[~, rcsValues] = RaytrAMP.LoadRcsFile('rcs360_3GHz_side.rcs');

%— POLAR PLOT IN dB —%
thetaPlot = deg2rad(azDeg);
r_dB      = 10*log10(rcsValues);

polarplot(thetaPlot, r_dB, 'LineWidth',1.5)
rlim([min(r_dB)-5, max(r_dB)+5])
thetaticks(0:45:315)
title('Monostatic RCS of ship @3 GHz, θ=0° (side view)')
ax = gca;
ax.RAxis.Label.String = 'RCS (dB·m^2)';
ax.FontSize = 12;

[~, shapeName, ~] = fileparts(unvName);  % Extract 'dihedral' from 'dihedral.unv'
filename = sprintf('%s_rcs360_3GHz_side.png', shapeName);
saveas(gcf, filename);
