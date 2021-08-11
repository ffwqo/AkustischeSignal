import numpy as np
import scipy.fft as fft
import dearpygui.dearpygui as dpg
import dearpygui.logger as dpg_logger
from util_def import *
from ook import OOKSimpleExp
from fdm import FDM
logger = dpg_logger.mvLogger()
dpg.hide_item(logger.window_id)

with dpg.font_registry():
    dpg.add_font("./SourceCodePro-Regular.ttf", 14, default_font=True)

indent = 40
storage = {}
storage_ook = {}
storage_fdm = {}
var_name_id_map = {} #flow choose var_name_id_map to get the id depending on the name i.e. "scp_mode" and access storage
var_name_id_map_ook = {}
var_name_id_map_fdm = {}

header_modulation_method = dpg.generate_uuid()
header_ook = dpg.generate_uuid()
header_fdm = dpg.generate_uuid()
log_checkbox_id = dpg.generate_uuid()
state = State() #TODO don't think I need plot_flag


def store_data(id, adata):
    storage[id] = adata
    logger.log(f"{storage}")
def store_data_ook(id, adata):
    storage_ook[id] = adata
    logger.log(f"{storage_ook}")

def store_data_fdm(id, adata):
    storage_fdm[id] = adata
    logger.log(f"{storage_fdm}")

def validate_bit_string_ook(id, data):
    if storage_ook[var_name_id_map_ook["generate"]] == True:
        bits = np.array(None)
        store_data_ook(id, bits)
        return
    print(data)
    if data == "":
        bits = np.array(None)
    else:
        bits = list(data)
        if (set(bits) != {"1"} and set(bits) != {"0"} and set(bits) != {"1", "0"}):
            print(' only "1" or "0" are valid characters for bits ')
            raise ValidationError
            bits = np.array(None)
        else:
            bits = [int(b) for b in bits]
            bits = np.array(bits)
    print(bits)
    store_data_ook(id, bits)

def validate_bit_string_fdm(id, data):
    if storage_fdm[var_name_id_map_fdm["generate"]] == True:
        bits = np.array(None)
        store_data_fdm(id, bits)
        return
    print(data)
    if data == "":
        bits = np.array(None)
    else:
        bits = list(data)
        if (set(bits) != {"1"} and set(bits) != {"0"} and set(bits) != {"1", "0"}):
            print(' only "1" or "0" are valid characters for bits ')
            raise ValidationError
            bits = np.array(None)
        else:
            bits = [int(b) for b in bits]
            bits = np.array(bits)
    print(bits)
    store_data_fdm(id, bits)

def save_osci_paramaters():
    state.osci_config = { k : storage[v] for k,v in var_name_id_map.items()}
    state.plot_flag = storage[var_name_id_map["plot_flag"]]
    state.osci_device = OsciDevice(state.osci_config)
    state.scp, state.gen = state.osci_device.setup()
    dpg.show_item(header_modulation_method)
    logger.log(f"osci_config: {state.osci_config}")
    logger.log(f"after setup scp: {state.scp} gen: {state.gen}")

def save_ook_parameter():
    state.modulation_config = { k : storage_ook[v] for k,v in var_name_id_map_ook.items()}
    method = OOKSimpleExp(
            Ts = state.modulation_config["ts"],
            fs = state.modulation_config["fs"],
            fc = state.modulation_config["fc"],
            Nbits = state.modulation_config["nbits"],
            generate = state.modulation_config["generate"])

    bits = state.modulation_config["bits"]
    if bits == "":
        bits = None
    signal = method.encode(bits)
    if state.plot_flag:
        with dpg.window(label="euikc"):
            with dpg.plot(label="signal plot", width=800, height=800):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="T [s]")
                dpg.add_plot_axis(dpg.mvYAxis, label="Y")
                dpg.add_line_series(method.t, signal, label="Encoded signal", parent=dpg.last_item())
        pass
    config = {**state.modulation_config, "scp_mode" : state.osci_config["scp_mode"]}
    state.measurment = Measurment(state.scp, state.gen, [signal], config)
    result = state.measurment.run()
    method.decode(result)

    logger.log(f"modulation_config: {state.modulation_config}")
    logger.log(f"method config: {config}")
    logger.log(f"signal: {signal}")
    logger.log(f"method internal bits: {method.bits}")
    logger.log(f"result bits: {result}")

def save_fdm_parameter():
    state.modulation_config = { k : storage_fdm[v] for k,v in var_name_id_map_fdm.items()}
    print(state.modulation_config)
    method = FDM(
            Ts = state.modulation_config["ts"],
            fs = state.modulation_config["fs"],
            fc = state.modulation_config["fc"],
            df = state.modulation_config["df"],
            Nbits = state.modulation_config["nbits"],
            generate = state.modulation_config["generate"])

    bits = state.modulation_config["bits"]
    if bits == "":
        bits = None
    signal = method.encode(bits)
    if state.plot_flag:
        with dpg.window(label="euikc"):
            with dpg.plot(label=f"bits: {list(method.bits.ravel())} spectrum plot", width=800, height=800):
                t = method.t
                spectrum = np.abs(fft.fft(signal))
                spectrum = spectrum[:len(spectrum // 2)]
                freq = fft.fftfreq(len(spectrum), t[1] - t[0])
                freq = freq[:len(spectrum // 2)]
                print(np.max(spectrum))
                logger.log_info(f"{spectrum}")
                logger.log_info(f"{freq}")
                logger.log_info(f"{len(freq) == len(spectrum)}")
                #freq = freq[:len(freq // 2)]
                dpg.add_plot_legend()
                axX = dpg.add_plot_axis(dpg.mvXAxis, label="f [Hz]")
                axY = dpg.add_plot_axis(dpg.mvYAxis, label="Y")
                dpg.add_line_series(freq, spectrum, label="Spectrum of encoded signal", parent=dpg.last_item())
                dpg.fit_axis_data(axX)
                dpg.fit_axis_data(axY)
        pass
    config = {**state.modulation_config, "scp_mode" : state.osci_config["scp_mode"]}
    state.measurment = Measurment(state.scp, state.gen, [signal], config)
    result = state.measurment.run()
    method.decode(result)

    logger.log(f"modulation_config: {state.modulation_config}")
    logger.log(f"method config: {config}")
    logger.log(f"signal: {signal}")
    logger.log(f"method internal bits: {method.bits}")
    logger.log(f"result bits: {result}")

def hide_header(id, data):
    if data == "OOK":
        dpg.show_item(header_ook)
        dpg.hide_item(header_fdm)
    elif data == "FDM":
        dpg.show_item(header_fdm)
        dpg.hide_item(header_ook)
    else:
        pass
def log_checkbox_callback(id, data):
    if data == True:
        dpg.show_item(logger.window_id)
    else:
        dpg.hide_item(logger.window_id)


with dpg.window(label="Main Window") as main_window:
    with dpg.menu_bar():
        with dpg.menu(label="Log"):
            dpg.add_checkbox(label="Show logger", default_value=False, id=log_checkbox_id, callback=log_checkbox_callback)

    with dpg.collapsing_header(label="Osci Parameter", default_open=True):

        #dpg.add_input_text(label="example", scientific=True, default_value=20e3, callback=lambda id, data: print(type(data)))
        plot_flag_id                    = dpg.add_checkbox(label="Plot", default_value=True, callback=store_data)
        dpg.add_text(default_value = "Scp measurement mode:")
        scp_mode_id                = dpg.add_radio_button(["STREAM", "BLOCK"], indent=indent, label="scp-mode", default_value="STREAM", horizontal=True, callback=store_data)
        scp_fs_id                  = dpg.add_input_float(label="[Hz] scp-fs", default_value=20e+03, min_value=0, max_value=1e9, user_data="scp-fs",callback=store_data)
        scp_record_length_id       = dpg.add_input_int(label="scp-record-length", default_value=10000, min_value=0, max_value=40000, callback=store_data)

        dpg.add_text(default_value="Generator signal type:")
        gen_signal_type_id         = dpg.add_radio_button(["ARBITRARY"],indent=indent, label="gen-signal-type", default_value="ARBITRARY", horizontal=True, callback=store_data)
        dpg.add_text(default_value="Generator frequency mode:")
        gen_freq_mode_id           = dpg.add_radio_button(["SAMPLEFREQUENCY"], indent=indent, label="gen-frequency-mode", default_value="SAMPLEFREQUENCY", horizontal=True, user_data="gen-freq-mode",callback=store_data)
        gen_fs_id                  = dpg.add_input_float(label="[Hz] gen-fs", default_value=20e+03, min_value=0, max_value=1e9, callback=store_data)
        gen_amp_id                 = dpg.add_input_float(label="[V] gen-amp", default_value=4.0, min_value=0, max_value=8, callback=store_data)
        gen_offset_id              = dpg.add_input_float(label="[V] gen-offset", default_value=0.0, min_value=0, max_value=1, callback=store_data)
        gen_output_on_id           = dpg.add_checkbox(label="Outpout on", default_value=True, callback=store_data)
        dpg.add_button(label="Save paramters", callback=save_osci_paramaters)

        var_name_id_map.update({ "plot_flag":         plot_flag_id,
                         "scp_mode":          scp_mode_id,
                         "scp_fs":            scp_fs_id,
                         "scp_record_length": scp_record_length_id,
                         "gen_signal_type":   gen_signal_type_id,
                         "gen_freq_mode":     gen_freq_mode_id,
                         "gen_fs":            gen_fs_id,
                         "gen_amp":           gen_amp_id,
                         "gen_offset":        gen_offset_id,
                         "gen_output_on":     gen_output_on_id })
        for k,v in var_name_id_map.items():
            storage[v] = dpg.get_value(v)
    with dpg.collapsing_header(label="Modulation Method", default_open=True, id= header_modulation_method, show=False):
        selection_id = dpg.add_radio_button(["OOK", "FDM"], horizontal=True, label="modulation-radio", default_value="OOK", callback=hide_header)
        with dpg.collapsing_header(indent=indent, label="OOK", id=header_ook, show=True, default_open=True):
            dpg.add_text("OOK")

            ts_ook_id                  = dpg.add_input_float(label="[s] Ts symbol duration##ook", default_value=30e-03, min_value=0, max_value=1.0, callback=store_data_ook)
            fs_ook_id                  = dpg.add_input_float(label="[Hz] fs sampling rate##ook", default_value=44e+03, min_value=0, max_value=1e+09, callback=store_data_ook)
            fc_ook_id                  = dpg.add_input_float(label="[Hz] fc carrier frequency##ook", default_value=1.8e+03, min_value=0, max_value=1e+09, callback=store_data_ook)
            nbits_ook_id                  = dpg.add_input_int(label="Nbits number of bits##ook", default_value=10, min_value=1, max_value=999, callback=store_data_ook)
            generate_ook_id                  = dpg.add_checkbox(label="wheter to generate bits##ook", default_value=True, callback=store_data_ook)
            bits_ook_id                  = dpg.add_input_text(label="bits to encode##ook", default_value="", decimal=True,callback=validate_bit_string_ook)
            dpg.add_button(label="Set OOK parameters", callback=save_ook_parameter)

            var_name_id_map_ook.update({
                    "ts" : ts_ook_id,
                    "fs" : fs_ook_id,
                    "fc" : fc_ook_id,
                    "nbits" : nbits_ook_id,
                    "generate" : generate_ook_id,
                    "bits" : bits_ook_id
                    })
            for k,v in var_name_id_map_ook.items():
                storage_ook[v] = dpg.get_value(v)
        with dpg.collapsing_header(indent=indent, label="FDM", id=header_fdm, show=False, default_open=True):
            dpg.add_text("FDM")

            ts_fdm_id                  = dpg.add_input_float(label="[s] Ts symbol duration##fdm", default_value=30e-03, min_value=0, max_value=1.0, callback=store_data_fdm)
            fs_fdm_id                  = dpg.add_input_float(label="[Hz] fs sampling rate##fdm", default_value=44e+03, min_value=0, max_value=1e+09, callback=store_data_fdm)
            fc_fdm_id                  = dpg.add_input_float(label="[Hz] fc carrier frequency##fdm", default_value=1.8e+03, min_value=0, max_value=1e+09, callback=store_data_fdm)
            df_fdm_id                  = dpg.add_input_float(label="[Hz] df frequency spacing##fdm", default_value=1e+02, min_value=0, max_value=1e+09, callback=store_data_fdm)
            nbits_fdm_id                  = dpg.add_input_int(label="Nbits number of bits##fdm", default_value=10, min_value=1, max_value=999, callback=store_data_fdm)
            generate_fdm_id                  = dpg.add_checkbox(label="wheter to generate bits##fdm", default_value=True, callback=store_data_fdm)
            bits_fdm_id                  = dpg.add_input_text(label="bits to encode##fdm", default_value="", decimal=True,callback=validate_bit_string_fdm)
            dpg.add_button(label="Set FDM parameters", callback=save_fdm_parameter)

            var_name_id_map_fdm.update({
                    "ts" : ts_fdm_id,
                    "fs" : fs_fdm_id,
                    "fc" : fc_fdm_id,
                    "df" : df_fdm_id,
                    "nbits" : nbits_fdm_id,
                    "generate" : generate_fdm_id,
                    "bits" : bits_fdm_id
                    })
            for k,v in var_name_id_map_fdm.items():
                storage_fdm[v] = dpg.get_value(v)
            print({ k: storage_fdm[v] for k,v in var_name_id_map_fdm.items()})


dpg.set_global_font_scale(2)
dpg.set_primary_window(main_window, True)
logger.log(f"{len(storage)} {storage}")
logger.log(f"{len(var_name_id_map)} {var_name_id_map}")
dpg.start_dearpygui()
