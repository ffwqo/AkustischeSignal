
if verLessThan('matlab', '8')
    error('Matlab 8.0 (R2012b) or higher is required.');
end

% Open LibTiePie and display library info if not yet opened:
import LibTiePie.Const.*
import LibTiePie.Enum.*

if ~exist('LibTiePie', 'var')
    % Open LibTiePie:
    LibTiePie = LibTiePie.Library
end

%%generate daata
x = 1:8192;
data = sin(x / 100) .* ( 1- (x / 8192));
clear x;


Nbits = 10
bits = rand(Nbits) < 0.5
fc = 10e+3
df = 100
fre = zeros(Nbits, 1)
lower = fc - Nbits * df
for i = 1:Nbits
    f = lower + i * 2 * df
    fre(i, 1) = f
A = 10
N = 8192
data = zeros(N, 1)
fs = 20e+3
T = 1 / fs;
x = linspace(0.0, N * T, N);
for i = 1:size(x)
    result = 0;
    for j = 1:Nbits
        result = result + bit * A * sin( 2 * pi * x)
    data(i, 1) = result;


%%%%


% Enable network search:       
LibTiePie.Network.AutoDetectEnabled = true;

% Search for devices:
LibTiePie.DeviceList.update();

% Try to open an oscilloscope with stream measurement support:
clear scp;
clear gen;
for k = 0 : LibTiePie.DeviceList.Count - 1
    item = LibTiePie.DeviceList.getItemByIndex(k);
    if (item.canOpen(DEVICETYPE.OSCILLOSCOPE)) && (item.canOpen(DEVICETYPE.GENERATOR))
        scp = item.openOscilloscope();
        if ismember(MM.STREAM, scp.MeasureModes)
            gen = item.openGenerator();
                %if ismember(ST.ARBITRARY, gen.SignalTypes)
            break;
        else
            clear scp;

        end
    end
end

if (exist('scp', 'var')) && (exist('gen', 'var'))
    % Set measure mode:
    scp.MeasureMode = MM.STREAM;

    % Set sample frequency:
    scp.SampleFrequency = 1e3; % 1 kHz

    % Set record length:
    scp.RecordLength = 1000; % 1 kS

    % For all channels:
    for ch = scp.Channels
        % Enable channel to measure it:
        ch.Enabled = true;

        % Set range:
        ch.Range = 8; % 8 V

        % Set coupling:
        ch.Coupling = CK.DCV; % DC Volt

        clear ch;
    end

    % Print oscilloscope info:
    display(scp);


    %do gen stuff
    gen.SignalType = ST.ARBITRARY;
    gen.FrequencyMode = FM.SAMPLEFREQUENCY;
    gen.Frequency = 100e3
    gen.Amplitude = 2;
    gen.OffSet = 0;
    gen.OutptOn = true;
    gen.setData(data);
    display(gen);

    %%%%%

    % Prepeare CSV writing:
    filename = 'OscilloscopeStream.csv';
    if exist(filename, 'file')
        delete(filename)
    end
    data = [];

    % Start measurement:
    gen.start();
    scp.start();

    % Measure 10 chunks:
    for k = 1 : 10
        % Display a message, to inform the user that we still do something:
        fprintf('Data chunk %u\n', k);

        % Wait for measurement to complete:
        while ~(scp.IsDataReady || scp.IsDataOverflow)
            pause(10e-3) % 10 ms delay, to save CPU time.
        end

        if scp.IsDataOverflow
            error('Data overflow!')
        end

        % Get data:
        newData = scp.getData();

        % Apped new data to plot:
        data = [data ; newData];
        figure(123);
        plot(data);

        % Append new data to CSV file:
        dlmwrite(filename, newData, '-append');
    end

    fprintf('Data written to: %s\n', filename);

    % Stop stream:
    scp.stop();
    gen.stop();

    % Close oscilloscope:
    clear scp;
    clear gen;
else
    error('No oscilloscope available with stream measurement support!');
end
