
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


function [result] = setup_and_run(mode, chunks, filename, scp_fs, scp_record_length, gen_fs, gen_amp, gen_offset, gen_output_on)
    % chunks should be a list of arrays chunks = {data1, ..., dataN} cell array
    % filename is where the result will be dumped

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
            if strcmp(mode, "STREAM")
                if ismember(MM.STREAM, scp.MeasureModes)
                    gen = item.openGenerator();
                    if ismember(ST.ARBITRARY, gen.SignalTypes)
                        break;
                        %if ismember(ST.ARBITRARY, gen.SignalTypes)
                    else 
                        clear gen;
                    end
                else
                    clear scp;
                end
            elseif strcmp(mode, "BLOCK")
                if ismember(MM.BLOCK, scp.MeasureModes)
                    gen = item.openGenerator();
                    if ismember(ST.ARBITRARY, gen.SignalTypes)
                        break;
                    else 
                        clear gen;
                    end
                else
                    clear scp;
                end
            else
            end
            else
                clear scp;
            end
        end
    end

    if (exist('scp', 'var')) && (exist('gen', 'var'))
        % Set measure mode:
        if strcmp(mode, "STREAM")
            scp.MeasureMode = MM.STREAM;
        elseif strcmp(mode, "BLOCK")
            scp.MeasureMode = MM.BLOCK;
        else
            error("Only STREAM or BLOCK allowed as mode")
        end

        % Set sample frequency:
        scp.SampleFrequency = scp_fs; %1e3; % 1 kHz

        % Set record length:
        scp.RecordLength = scp_record_length; %1000; % 1 kS

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
        gen.Frequency = gen_fs; %100e3
        gen.Amplitude = gen_amp; %2;
        gen.OffSet = gen_offset; %0;
        gen.OutptOn = gen_output_on; %true;
        display(gen);

        %%%%%

        gen.setData(data);
        % Prepeare CSV writing:
        if exist(filename, 'file')
            error("%s already exists", filename)
        end
        data = [];

        for i=1:length(chunks)
            gen.setData(chunks{1, k})
        % Start measurement:
            gen.start();
            scp.start();

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
            %dlmwrite(filename, newData, "-append");
            writeMatrix(newData, filename, "WriteMode", "append");
            gen.stop();

        end
        scp.stop();

        result = data

        fprintf('Data written to: %s\n', filename);

        % Stop stream:

        % Close oscilloscope:
        clear scp;
        clear gen;
    else
        error('No oscilloscope available with stream measurement support!');
    end
end
