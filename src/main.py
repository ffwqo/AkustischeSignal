#TODO plot flag?
import matplotlib.pyplot as plt
import click
import sys
import os
import time
import numpy as np
from array import array
import libtiepie
from printinfo import *

from ook import OOKSimpleExp
from fdm import FDMSimple as FDM

class State():
    def __init__(self):
        self.scp = None
        self.gen = None
        self.plot_flag = True
        self.osci_config = None
        self.osci_device = None
        self.modulation_config = None
        self.measurement = None
        self.modulation_method = None

pass_state = click.make_pass_decorator(State)

class MeasurmentFailure(Exception):
    pass
class ValidationError(Exception):
    pass
class Measurment():
    """
        to use firs define your ModulationMethodClass()
        then call encode and save the signal
        signal = encode() or signal = encode(bits)
        finally wrap signal around [signal] and init Measurment(scp, gen, chunks)
        scp, gen come from OsciDevice.setup()
    """
    def __init__(self, scp, gen, chunks, config_dict):
        assert(scp != None)
        assert(gen != None)
        assert(config_dict != None)
        assert(len(chunks) ==1 and config_dict["mode"] == "BLOCK")
        self.scp = scp
        self.gen = gen
        self.chunks = [array("f", chunk) for chunk in chunks]
        self.config_dict = config_dict
        print("Starting measurment!")
    def set_parameters_osci(self, osci_device, debug=False):
        assert( isinstance(osci_device, OsciDevice))
        if self.scp and self.gen:
            try:
                self.scp.measure_mode = osci_device.scp_mode          
                self.scp.sample_frequency = osci_device.scp_fs            
                self.scp.record_length = osci_device.scp_record_length 
                for ch in self.scp.channels:
                    ch.enabled = True
                    ch.range = 8
                    ch.coupling = libtiepie.CK_DCV

                self.gen.signal_type    = osci_device.gen_signal_type
                self.gen.frequency_mode = osci_device.gen_freq_mode
                self.gen.frequency      = osci_device.gen_fs
                self.gen.amplitude      = osci_device.gen_amp
                self.gen.offset         = osci_device.gen_offset
                self.gen.output_on      = osci_device.gen_output_on
                if debug:
                    print_device_info(self.scp)
                    print_device_info(self.gen)
            except Exception as e:
                click.echo("Exception: " + str(e))
                click.echo(sys.exc_info()[0])
                return
                #sys.exit(1)
        click.echo("Successfully set osci parameters")

    def run(self):
        scp = self.scp
        gen = self.gen
        chunks = self.chunks
        mode = self.config_dict["scp_mode"] #string
        result = []
        try:
            scp.start()
            for i in range(len(chunks)):
                gen.set_data(chunks[i])
                gen.start()

                while not (scp.is_data_ready or scp.is_data_overflow):
                    time.sleep(0.01)
                if scp.is_data_overflow:
                    click.echo("Data overflow")
                d = np.array(scp.get_data())
                """
                scp returns data like 
                     --------->
                #Ch1 | 2 3 5 6 
                #Ch2 | 2 -3 -2 -2
                     V
                result[i] looks like
                | 2 2
                | 3 -3
                | 5 -2
                V 6  -2
                """
                result.append(d.transpose())
                gen.stop()
            scp.stop()

            #result will be a list of data arrays need to append them each other
            #TODO might have to transpose first
            #TODO need to figure out the right order here
            data = np.concatenate(result)

            header = ""
            i = 0
            filename = f"measure_data_{mode}.txt"
            while os.path.isfile(filename):
                filename = f"measure_data_{i}_{mode}.txt"
                i += 1

            for i in range(len(scp.channels)):
                header += f"Ch{i+1}\t"
            np.savetxt(filename, np.array(data).transpose(), header=header)
        except:
            click.echo("Cannot start measurement")
            raise MeasurmentFailure
        click.echo("Finished measurement")
        return result

class OsciDevice():
    def __init__(self, config_dict):
        assert(config_dict != None)

        self.scp_mode_map            = { libtiepie.MM_BLOCK : "BLOCK", libtiepie.MM_STREAM : "STREAM"}
        scp_mode_reverse_map    = { v: k for k,v in self.scp_mode_map.items()}
        gen_signal_type_map = {"ARBITRARY" : libtiepie.ST_ARBITRARY}
        gen_freq_mode_map   = {"SAMPLEFREQUENCY" : libtiepie.FM_SAMPLEFREQUENCY}


        self.scp = None
        self.gen = None
        self.scp_mode          = scp_mode_reverse_map[config_dict["scp_mode"]] #grabs a libtiepie.MM_{BLOCK, STREAM}
        self.scp_fs            = config_dict["scp_fs"]
        self.scp_record_length = config_dict["scp_record_length"]
        self.gen_signal_type   = gen_signal_type_map[config_dict["gen_signal_type"]]
        self.gen_freq_mode     = gen_freq_mode_map[config_dict["gen_freq_mode"]]
        self.gen_fs            = config_dict["gen_fs"]
        self.gen_amp           = config_dict["gen_amp"]
        self.gen_offset        = config_dict["gen_offset"]
        self.gen_output_on    = config_dict["gen_output_on"]
    def setup(self, debug=False):
        if debug:
            print_device_info()
        libtiepie.network.auto_detect_enabled = True
        libtiepie.device_list.update()

        self.scp_dict = {}
        self.gen_dict = {}
        scp = None
        gen = None

        #first scp+gen for MM_BLOCK
        for item in libtiepie.device_list:
            if ( item.can_open(libtiepie.DEVICETYPE_OSCILLOSCOPE)) and (item.can_open(libtiepie.DEVICETYPE_GENERATOR)):
                scp = item.open_oscilloscope()
                if scp.measure_modes & libtiepie.MM_BLOCK:
                    gen = item.open_generator()
                    if gen.signal_type & libtiepie.ST_ARBITRARY:
                        break
                else:
                    scp = None
        if scp != None:
            self.scp_dict[libtiepie.MM_BLOCK] = scp
            self.gen_dict[libtiepie.MM_BLOCK] = gen
        else:
            click.echo("SCP/GEN NOT FOUND FOR MM_BLOCK from main.py")

        scp = None
        gen = None
        #then scp+gen for MM_STREAM
        for item in libtiepie.device_list:
            if ( item.can_open(libtiepie.DEVICETYPE_OSCILLOSCOPE)) and (item.can_open(libtiepie.DEVICETYPE_GENERATOR)):
                scp = item.open_oscilloscope()
                if scp.measure_modes & libtiepie.MM_STREAM:
                    gen = item.open_generator()
                    if gen.signal_type & libtiepie.ST_ARBITRARY:
                        break
                else:
                    scp = None
        if scp != None:
            self.scp_dict[libtiepie.MM_STREAM] = scp
            self.gen_dict[libtiepie.MM_STREAM] = gen
        else:
            click.echo("SCP/GEN NOT FOUND FOR MM_STREAM from main.py")

        if self.scp_mode in self.scp_dict:
            self.scp = self.scp_dict[self.scp_mode]
            self.gen = self.gen_dict[self.scp_mode]
        else:
            self.scp = None
            self.gen = None



        if self.scp and self.gen:
            try:
                self.scp.measure_mode = self.scp_mode          
                self.scp.sample_frequency = self.scp_fs            
                self.scp.record_length = self.scp_record_length 
                for ch in self.scp.channels:
                    ch.enabled = True
                    ch.range = 8
                    ch.coupling = libtiepie.CK_DCV

                self.gen.signal_type    = self.gen_signal_type
                self.gen.frequency_mode = self.gen_freq_mode
                self.gen.frequency      = self.gen_fs
                self.gen.amplitude      = self.gen_amp
                self.gen.offset         = self.gen_offset
                self.gen.output_on      = self.gen_output_on
                if debug:
                    print_device_info(scp)
                    print_device_info(gen)
            except Exception as e:
                click.echo("Exception: " + str(e))
                click.echo(sys.exc_info()[0])
                return
                #sys.exit(1)
        else:
            click.echo("No device avaible for measurement in " + self.scp_mode_map[self.scp_mode] + " mode")
        click.echo("Successfully set")
        return self.scp, self.gen


def validate_bit_string(kwargs):
    bits = None
    if kwargs["bits"] == "":
        bits = np.array(None)
    else:
        bits = list(kwargs["bits"])
        if set(bits) != {"1", "0"} and not kwargs["generate"]:
            print(' only "1" or "0" are valid characters for bits ')
            raise ValidationError
            bits = np.array(None)
        else:
            bits = np.array([int(b) for b in bits])
    return bits



CONTEXT_SETTINGS = dict(
    show_default=True
)

#=============OSCI
@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.option("--plot/--no-plot", default=True)
@click.option("--stream", "scp_mode", flag_value="STREAM", help="scp STREAM mode")
@click.option("--block", "scp_mode", flag_value="BLOCK", help="scp BLOCK mode", default=True)
@click.option("--scp-fs", type=click.FLOAT, default=20e3, help="scp sampling rate fs")
@click.option("--scp-record-length", type=click.INT, default=10000, help="scp record_length")
@click.option("--gen-signal-type-ARBITRARY", "gen_signal_type", flag_value="ARBITRARY", help="generator signal type only ARBITRARY implemented [default]", default=True)
@click.option("--gen-frequency-mode", "gen_freq_mode", flag_value="SAMPLEFREQUENCY", help="generator frequency mode only SAMPLEFREQUENCY implemented [default]", default=True)
@click.option("--gen-fs", type=click.FLOAT, default=20e3, help="generator sampling rate")
@click.option("--gen-amp", type=click.FLOAT, default=4.0, help="generator Amplitude")
@click.option("--gen-offset", type=click.FLOAT, default=0.0, help="generator offet")
@click.option("--gen-output-on", type=click.BOOL, default=True, help="generator Offset on")
@click.pass_context
def cli(ctx, plot, **kwargs):
    ctx.obj = State()
    ctx.obj.osci_config = kwargs
    ctx.obj.osci_device = OsciDevice(kwargs)
    ctx.obj.scp, ctx.obj.gen = ctx.obj.osci_device.setup()
    #click.echo(kwargs)
    ctx.obj.plot_flag = plot


#=============OOK
@cli.command()
@click.option("--modulation-method", "modulation_method", flag_value="OOK", help="modulation method", default=True)
@click.option("--ts", type=click.FLOAT, default=30e-03, help="symbol duration Ts")
@click.option("--fs", type=click.FLOAT, default=44000, help="sampling rate fs")
@click.option("--fc", type=click.FLOAT, default=1800, help="carrier frequency fc")
@click.option("--nbits", type=click.INT, default=10, help="number of bits to encode")
@click.option("--generate", type=click.BOOL, default=True, help="wether to randomly generate bits")
@click.option("--bits", type=click.STRING, default="", help="bit sequence")
@pass_state
def ook(state, **kwargs):
    state.modulation_config = kwargs 
    method = OOKSimpleExp( Ts=kwargs["ts"], 
            fs=kwargs["fs"],
            fc=kwargs["fc"],
            Nbits=kwargs["nbits"],
            generate=kwargs["generate"])

    bits = validate_bit_string(kwargs)
    bits = np.array([int(i) for i in (np.random.rand(kwargs["nbits"]) > 0.5)])
    print("Input bit array: ", bits)
    signal = method.encode(bits)
    if state.plot_flag == True :
        method.plot(signal, bits)

    config = {**kwargs, "scp_mode" : state.osci_config["scp_mode"]}
    state.measurement = Measurment(state.scp, state.gen, [signal], config)
    result = state.measurement.run()
    method.decode(result)



#=============FDM
@cli.command()
@click.option("--modulation-method", "modulation_method", flag_value="FDM", help="modulation method", default=True)
@click.option("--ts", type=click.FLOAT, default=30e-03, help="symbol duration Ts")
@click.option("--fs", type=click.FLOAT, default=44000, help="sampling rate fs")
@click.option("--fc", type=click.FLOAT, default=1800, help="carrier frequency fc")
@click.option("--df", type=click.FLOAT, default=100, help="frequency spacing used")
@click.option("--nbits", type=click.INT, default=10, help="number of bits to encode")
@click.option("--generate", type=click.BOOL, default=True, help="wether to randomly generate bits")
@click.option("--bits", type=click.STRING, default="", help="bit sequence")
@pass_state
def fdm(state, **kwargs):
   #TODO check fdm.encdode fdm.decode implement with signal, bits 
    state.modulation_config = kwargs 
    method = FDM( Ts=kwargs["ts"], 
            fs=kwargs["fs"],
            fc=kwargs["fc"],
            df=kwargs["df"],
            Nbits=kwargs["nbits"],
            generate=kwargs["generate"])

    bits = validate_bit_string(kwargs)
    bits = np.array([int(i) for i in (np.random.rand(kwargs["nbits"]) > 0.5)])
    print("Input bit array: ", bits)
    signal = method.encode(bits)
    if state.plot_flag == True :
        method.plot(signal, bits)

    config = {**kwargs, "scp_mode" : state.osci_config["scp_mode"]}
    state.measurement = Measurment(state.scp, state.gen, [signal], config)
    result = state.measurement.run()
    method.decode(result)


if __name__ =="__main__":
    cli()

