import math
from iqdbc.car.volkswagen.mqbcan import (volkswagen_mqb_meb_checksum, xor_checksum,
                                         acc_control_value as mqb_acc_control_value,
                                         acc_hud_status_value as mqb_acc_hud_status_value,
                                         create_lka_hud_control as mqb_create_lka_hud_control)


def create_hca_steering_control(packer, bus, apply_steer, HCA_Status):
  values = {
    "HCA_01_Status_HCA": HCA_Status,
    "HCA_01_LM_Offset": abs(apply_steer),
    "HCA_01_LM_OffSign": 1 if apply_steer < 0 else 0,
    "HCA_01_Vib_Freq": 18,
    "HCA_01_Sendestatus": 1 if HCA_Status in (5, 7) else 0,
  }
  return packer.make_can_msg("HCA_01", bus, values)


ALC_PLA_01_ADDR = 0x130


def create_alc_angle_control(packer, bus, angle_deg):
  # Private tunnel to the standalone ALC panda module: a PLA_01-shaped frame
  # sent directly by OP on the car bus. 0x130 never appears there in stock
  # traffic (the module is the sole real source of PLA_01, and only on the
  # EPS-side bus), so this can't collide with anything real or with IQ's own
  # HCA_01-based control path. Angle uses the same 0.1 deg/bit raw scale as
  # LWI_Lenkradwinkel, matching what the module expects (PLA_LW_Soll's bit
  # position but not its native 0.04375 deg/bit resolution).
  if not math.isfinite(angle_deg):
    angle_deg = 0.0
  angle_raw = min(int(round(abs(angle_deg) * 10)), 0x1FFF)
  sign = 1 if angle_deg < 0 else 0

  dat = bytearray(8)
  dat[2] = angle_raw & 0xFF
  dat[3] = ((angle_raw >> 8) & 0x1F) | (sign << 7)

  return ALC_PLA_01_ADDR, bytes(dat), bus


def create_lka_hud_control(packer, bus, ldw_stock_values, enabled, steering_pressed, hud_alert, hud_control,
                           entering=False, special_mode=False, special_active=False):
  return mqb_create_lka_hud_control(packer, bus, ldw_stock_values, enabled, steering_pressed, hud_alert, hud_control,
                                    entering, special_mode, special_active)


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
  if cruiseOverride:
    acc_control = 4
  elif accFaulted:
    acc_control = 6
  elif long_active:
    acc_control = 3
  elif main_switch_on:
    acc_control = 2
  else:
    acc_control = 0

  return acc_control


def acc_hud_status_value(main_switch_on, acc_faulted, longActive, longOverride):
  return mqb_acc_hud_status_value(main_switch_on, acc_faulted, longActive, longOverride)


def create_acc_accel_control(packer, bus, accel, acc_control, stopping):
  acc_enabled = acc_control in (3, 4)

  acc_01_values = {
    "ACC_Status_ACC": acc_control,
    "ACC_Sollbeschleunigung": accel if acc_enabled else 0,
    "ACC_zul_Regelabw_unten": 0.2 if acc_enabled else 0,
    "ACC_zul_Regelabw_oben": 0.2 if acc_enabled else 0,
    "ACC_neg_Sollbeschl_Grad": 4.0 if acc_enabled else 0,
    "ACC_pos_Sollbeschl_Grad": 4.0 if acc_enabled else 0,
    "ACC_Dynamik": 3,
    "ACC_Anhalten": stopping if acc_enabled else False,
    "ACC_Minimale_Bremsung": 0,
  }

  return [packer.make_can_msg("ACC_01", bus, acc_01_values)]


def create_acc_hud_control(packer, bus, acc_hud_status, set_speed, leadDistance, distanceBars, fcw_alert, leadVisible,
                           unavailable, decel, d_unresponsive, hud_text=0, desired_distance=8.0):
  engaged = acc_hud_status in (3, 4)
  priodisp = 0 if fcw_alert else 1 if (acc_hud_status == 4 or decel or leadVisible) else 2 if (acc_hud_status in (3, 2)) else 0
  if not engaged:
    acc_distance_index = 1022
  elif not leadVisible:
    acc_distance_index = 1023
  else:
    distance_ratio = leadDistance / max(desired_distance, 1.0)
    acc_distance_index = int(max(1, min(1021, round(490 * (3 - 2 * distance_ratio)))))

  values = {
    "ACC_Status_Anzeige": acc_hud_status,  # 0 off, 1 init, 2 standby, 3 active, 4 overridden, 5 shutdown reaction, 6/7 fault
    "ACC_Wunschgeschw_02": set_speed if set_speed < 250 else 327.36,  # 327.36 (raw 1023) = "no display"
    "ACC_Gesetzte_Zeitluecke": distanceBars,  # 1 aggressive, 2 standard, 3 relaxed
    "ACC_Anzeige_Zeitluecke": 1 if engaged else 0,  # 0 gap bars not requested, 1 requested
    "ACC_Tachokranz": 1 if engaged else 0,          # 0 speedo ring not lit, 1 lit
    "ACC_Display_Prio": priodisp,  # 0 highest prio, 1 medium, 2 low, 3 none
    "ACC_Abstandsindex": acc_distance_index, # 1 - 1020 = Lead distance, 1021 = Emergency brake alert, 1022 = ACC off, 1023 = ACC on but no lead
    "ACC_Relevantes_Objekt": 2 if fcw_alert else (1 if leadVisible else 0),  # lead car: 1 green, 2 red, 0 off
    "ACC_Status_Prim_Anz": 2 if fcw_alert else (1 if engaged else 0),        # ACC symbol: 1 green, 2 red, 3 yellow, 0 off
    "ACC_Optischer_Fahrerhinweis": 1 if fcw_alert else 0, # 0 = off, 1 = on
    "ACC_Akustik": 1 if (fcw_alert or d_unresponsive) else 0,  # 0 none, 1 high prio, 2 low prio, 3 high prio continuous
    "ACC_Texte_Primaeranz": hud_text,  # primary HUD message text code, e.g. 10 "ACC ready", 53 "ACC off" (see DBC VAL_ for full list)
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
