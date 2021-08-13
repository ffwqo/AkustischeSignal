# install matlab engine https://de.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html
import matlab.engine
eng = matlab.engine.start_matlab()
#setup_and_run(mode, chunks, filename, scp_fs, scp_record_length, gen_fs, gen_amp, gen_offset, gen_output_on)

ret = eng.setup_and_run("STREAM", [signal], filename, scp_fs, scp_record_length, gen_fs, gen_amp, gen_offset, gen_output_on)
