from iqdbc.car.volkswagen.mqbcan import (volkswagen_mqb_meb_checksum, xor_checksum, create_lka_hud_control as mqb_create_lka_hud_control)

def create_hca_steering_control(packer, bus, apply_steer, HCA_Status):
  values = {
    "HCA_01_Status_HCA": HCA_Status,
    "HCA_01_LM_Offset": abs(apply_steer),
    "HCA_01_LM_OffSign": 1 if apply_steer < 0 else 0,
    "HCA_01_Vib_Freq": 18,
    "HCA_01_Sendestatus": 1 if HCA_Status in (5, 7) else 0,
  }
  return packer.make_can_msg("HCA_01", bus, values)


def create_lka_hud_control(packer, bus, ldw_stock_values, enabled, steering_pressed, hud_alert, hud_control, entering=False, special_mode=False, special_active=False):
  return mqb_create_lka_hud_control(packer, bus, ldw_stock_values, enabled, steering_pressed, hud_alert, hud_control, entering, special_mode, special_active)


def create_acc_buttons_control(packer, bus, gra_stock_values, cancel=False, resume=False, set_button=False):
  values = {s: gra_stock_values[s] for s in [
    "LS_Hauptschalter",
    "LS_Typ_Hauptschalter",
    "LS_Codierung",
    "LS_Tip_Stufe_2",
  ]}

  values.update({
    "COUNTER": (gra_stock_values["COUNTER"] + 1) % 16,
    "LS_Abbrechen": cancel,
    "LS_Tip_Wiederaufnahme": resume,
  })

  return packer.make_can_msg("LS_01", bus, values)


def acc_control_value(main_switch_on, long_active, cruiseOverride, accFaulted):
  if accFaulted:
    acc_control = 6
  elif long_active or cruiseOverride:
    acc_control = 3
  elif main_switch_on:
    acc_control = 2
  else:
    acc_control = 0

  return acc_control


def acc_hud_status_value(main_switch_on, acc_faulted, longActive, longOverride):
  return 0


def create_acc_accel_control(packer, bus, acc_type, accel, acc_control, stopping, starting, esp_hold,
                              comfortBand, jerkLimit, eBrakeActive, sng_active=False):
  commands = []
  acc_enabled = acc_control == 3

  acc_01_values = {
    "ACC_Status_ACC": acc_control,
    "ACC_Sollbeschleunigung": accel if acc_enabled else 0,
    "ACC_zul_Regelabw_unten": comfortBand if acc_enabled else 0.2,
    "ACC_zul_Regelabw_oben": comfortBand if acc_enabled else 0.2,
    "ACC_neg_Sollbeschl_Grad": jerkLimit if acc_enabled else 4.0,
    "ACC_pos_Sollbeschl_Grad": jerkLimit if acc_enabled else 4.0,
    "ACC_Dynamik": 3,
    "ACC_Anhalten": stopping or eBrakeActive,
  }
  commands.append(packer.make_can_msg("ACC_01", bus, acc_01_values))

  return commands


def create_acc_hud_control(packer, bus, acc_hud_status, set_speed, leadDistance, distanceBars, fcw_alert, leadVisible, unavailable, decel, d_unresponsive):
  active = acc_hud_status == 3
  chime = fcw_alert or d_unresponsive
  values = {
    "ACC_Status_Anzeige": acc_hud_status,
    "ACC_Wunschgeschw_02": set_speed if set_speed < 250 else 327.04,
    "ACC_Display_Prio": 1 if active else 0,
    "ACC_Anzeige_Zeitluecke": 1 if active else 0,
    "ACC_Gesetzte_Zeitluecke": distanceBars,
    "ACC_Tachokranz": 1 if active else 0,
    "ACC_Relevantes_Objekt": 2 if fcw_alert else (1 if active and leadVisible else 0),
    "ACC_Status_Prim_Anz": 2 if fcw_alert else (1 if active and leadVisible else 0),
    "ACC_Akustik": 1 if chime else 0,
    "ACC_Abstandsindex": 1023 if active else 1022,
  }
  return packer.make_can_msg("ACC_02", bus, values)

def volkswagen_mlb_checksum(address: int, sig, d: bytearray) -> int:
  xor_starting_value = {
    0x109: 0x08, # ACC_01
    0x111: 0x10, # TSK_05
    0x30C: 0x0F, # ACC_02
    0x324: 0x27, # ACC_04
    0x10B: 0xA,  # LS_01
    0x10D: 0x0C, # ACC_05
    0x10F: 0x0E, # ACC_0x10F
    0x311: 0x12, # ACC_0x311
    0x397: 0x94, # LDW_02
    0x10C: 0x0D, # TSK_02
  }
  if address in xor_starting_value:
    return xor_checksum(address, sig, d, xor_starting_value[address])
  else:
    return volkswagen_mqb_meb_checksum(address, sig, d)
