/* SPDX-License-Identifier: GPL-3.0-only
 * Stable NRPN v1 wire addresses. Never reindex or reuse retired addresses.
 * Names are consumed by the Hapax generator, not stored in firmware. */
#ifndef FELUCCA_MIDI_NRPN_MAP_H
#define FELUCCA_MIDI_NRPN_MAP_H

#define MIDI_NRPN_COMMON(X) \
    X(0, P_LEVEL, "Nivel") \
    X(1, P_ATK, "ENV Ataque") \
    X(2, P_DEC, "ENV Decaimiento") \
    X(3, P_SUS, "ENV Sostenido") \
    X(4, P_REL, "ENV Liberacion") \
    X(5, P_ED_FLT, "ENV Filtro") \
    X(6, P_ED_PIT, "ENV Tono") \
    X(7, P_ED_SHP, "ENV Forma") \
    X(9, P_LRATE, "LFO Frecuencia") \
    X(10, P_LWAVE, "LFO Onda") \
    X(11, P_LPHASE, "LFO Fase") \
    X(12, P_LFADE, "LFO Entrada") \
    X(13, P_LD_PIT, "LFO Tono") \
    X(14, P_LD_FLT, "LFO Filtro") \
    X(15, P_LD_SHP, "LFO Forma") \
    X(16, P_LD_AMP, "LFO Amplitud") \
    X(17, P_AMODE, "Arp Modo") \
    X(18, P_ARATE, "Arp Frecuencia") \
    X(19, P_AOCT, "Arp Octavas") \
    X(20, P_AGATE, "Arp Duracion") \
    X(21, P_ASWING, "Arp Swing") \
    X(22, P_APROB, "Arp Probabilidad") \
    X(23, P_AHOLD, "Arp Retener") \
    X(24, P_AORDER, "Arp Orden") \
    X(25, P_ROOT, "Escala Raiz") \
    X(26, P_SCALE, "Escala") \
    X(27, P_QUANT, "Cuantizar") \
    X(28, P_TRANS, "Transposicion") \
    X(29, P_SLEN, "Secuencia Longitud") \
    X(30, P_SDIV, "Secuencia Division") \
    X(31, P_SSWING, "Secuencia Swing") \
    X(32, P_SGATE, "Secuencia Duracion") \
    X(33, P_DIST, "Distorsion") \
    X(34, P_CHOR, "Envio Chorus") \
    X(35, P_DLY, "Envio Delay") \
    X(36, P_REV, "Envio Reverb") \
    X(37, P_VOICE, "Voz Modo") \
    X(38, P_GLIDE, "Portamento") \
    X(39, P_PAN, "Panorama") \
    X(40, P_MUTE, "Silencio") \
    X(41, P_GLMODE, "Portamento Modo") \
    X(42, P_PRIO, "Voz Prioridad") \
    X(43, P_ALLOC, "Voz Asignacion") \
    X(44, P_DETUNE, "Desafinacion") \
    X(45, P_SLCR, "Slicer Modo") \
    X(46, P_SLPAT, "Slicer Patron") \
    X(47, P_SLRATE, "Slicer Frecuencia") \
    X(48, P_SLDEPTH, "Slicer Profundidad") \
    X(49, P_M1SRC, "Matriz1 Fuente") \
    X(50, P_M1DST, "Matriz1 Destino") \
    X(51, P_M1AMT, "Matriz1 Cantidad") \
    X(52, P_M2SRC, "Matriz2 Fuente") \
    X(53, P_M2DST, "Matriz2 Destino") \
    X(54, P_M2AMT, "Matriz2 Cantidad") \
    X(55, P_M3SRC, "Matriz3 Fuente") \
    X(56, P_M3DST, "Matriz3 Destino") \
    X(57, P_M3AMT, "Matriz3 Cantidad") \
    X(58, P_M4SRC, "Matriz4 Fuente") \
    X(59, P_M4DST, "Matriz4 Destino") \
    X(60, P_M4AMT, "Matriz4 Cantidad") \
    X(81, P_CHRD, "Acorde") \
    X(82, P_VOIC, "Voces Acorde") \
    X(83, P_LN0, "Bateria Bombo") \
    X(84, P_LN1, "Bateria Caja") \
    X(85, P_LN2, "Bateria Palmas") \
    X(86, P_LN3, "Bateria Hat Cerrado") \
    X(87, P_LN4, "Bateria Hat Abierto") \
    X(88, P_LN5, "Bateria Tom") \
    X(89, P_LN6, "Bateria Aro") \
    X(90, P_LN7, "Bateria Campana") \
    X(91, P_LSYNC, "LFO Sync") \
    X(92, P_LTRIG, "LFO Disparo") \
    X(93, P_LPOL, "LFO Polaridad") \
    X(94, P_SQNT, "Secuencia Cuantizar") \
    X(95, P_SPRD, "Apertura") \
    X(96, P_ITYPE, "Insert Tipo") \
    X(97, P_IA, "Insert A") \
    X(98, P_IB, "Insert B") \
    X(99, P_IC, "Insert C") \
    X(100, P_IMIX, "Insert Mezcla") \
    X(101, P_FTYPE, "Analog Filtro Tipo") \
    X(102, P_ESYNC, "ENV Sync")

#define MIDI_NRPN_ENGINE(X) \
    X(0, P_E0, "Motor E1") \
    X(1, P_E1, "Motor E2") \
    X(2, P_E2, "Motor E3") \
    X(3, P_E3, "Motor E4") \
    X(4, P_E4, "Motor E5") \
    X(5, P_E5, "Motor E6") \
    X(6, P_E6, "Motor E7") \
    X(7, P_E7, "Motor E8")

#endif
