% TODO investigate python package integration https://de.mathworks.com/help/compiler_sdk/python_packages.html
% TODO util.m implement setup. set_parameters_osci, run

if verLessThan('matlab', '8')
    error('Matlab 8.0 (R2012b) or higher is required.');
end

% Open LibTiePie and display library info if not yet opened:
import LibTiePie.Const.*
import LibTiePie.Enum.*
% Enable network search:       
LibTiePie.Network.AutoDetectEnabled = true;
% Search for devices:
LibTiePie.DeviceList.update();

if ~exist('LibTiePie', 'var')
    % Open LibTiePie:
    LibTiePie = LibTiePie.Library
end

function [scp, gen] = osci_setup_init(mode, debug)
    % returns scp and gen for mode STREAM or BLOCK
    clear scp;
    clear gen;
    for k = 0 : LibTiePie.DeviceList.Count - 1
        item = LibTiePie.DeviceList.getItemByIndex(k);
        if (item.canOpen(DEVICETYPE.OSCILLOSCOPE)) && (item.canOpen(DEVICETYPE.GENERATOR))
            scp = item.openOscilloscope();
            if strcmp(mode, "STREAM")
                if ismember(MM.STREAM, scp.MeasureModes)
                    gen = item.openGenerator();
                        %if ismember(ST.ARBITRARY, gen.SignalTypes)
                    break;
                end
            elseif strcmp(mode, "BLOCK")
                if ismember(MM.BLOCK, scp.MeasureModes)
                    gen = item.openGenerator();
                        %if ismember(ST.ARBITRARY, gen.SignalTypes)
                    break;
                end
            else
                % fprintf("Error src and gen not found")
                error("Error src and gen not found")
            end
        end
    end
    % TODO handle None case?

end
function [scp, gen] = osci_set_parameters(scp, gen, mode, fs, record_length, gen_signal_type, gen_freq_mode, gen_fs, gen_amp, gen_offset, gen_output_on)
    % sets the osci parameters
    % hack because I have no idea how to check if scp and gen are valid inputs.
end
function [result] = osci_run(scp, gen, mode, chunks)
    % starts the measurment accpeting a list of data as chunks... TODO
end

function [] = osci_stop_scp_gen(scp, gen)
    scp.stop()
    gen.stop()
end



%%%%



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
