#!/usr/bin/env python3
"""Generic junction / heat-sink calculator.

Steady state, single shot and back-to-back duty for one power device on a heat sink.

Examples
    thermal.py --rjc 0.35 --rcs 0.36 --rsa 1.05 --ta 35 --tj 110 --power 36
    thermal.py --rjc 0.35 --rcs 0.36 --rsa 1.05 --mass-g 150 --power 50 --t-on 10 --t-off 5
Take --rsa from the manufacturer's Rth-versus-length curve for the ordered length,
never from a distributor field. --mass-g is an assumption when the datasheet gives none.
"""
import argparse
import math

CP_AL = 0.897  # J/(g K), aluminium


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--rjc', type=float, required=True, help='junction-to-case, K/W')
    ap.add_argument('--rcs', type=float, required=True, help='case-to-sink incl. paste and insulator, K/W')
    ap.add_argument('--rsa', type=float, required=True, help='sink-to-ambient at ordered length, K/W')
    ap.add_argument('--ta', type=float, default=35.0, help='ambient C')
    ap.add_argument('--tj', type=float, default=110.0, help='design junction limit C')
    ap.add_argument('--power', type=float, nargs='+', required=True, help='dissipation(s) W')
    ap.add_argument('--mass-g', type=float, default=0.0, help='sink mass g (enables transient)')
    ap.add_argument('--t-on', type=float, default=0.0, help='on time s per test (enables back-to-back)')
    ap.add_argument('--t-off', type=float, default=0.0, help='pause s between tests')
    ap.add_argument('--tsink-start', type=float, default=70.0, help='sink limit to start a full-power test, C')
    ap.add_argument('--tsink-cut', type=float, default=80.0, help='hardware cut-off sink temperature, C')
    ap.add_argument('--tests', type=int, default=400, help='max back-to-back tests simulated')
    a = ap.parse_args()

    path = a.rjc + a.rcs
    total = path + a.rsa
    print(f'Rjc+Rcs = {path:.2f} K/W, total = {total:.2f} K/W, Ta = {a.ta} C, Tj limit = {a.tj} C')
    print(f'Continuous power limit: {(a.tj - a.ta) / total:.1f} W')
    C = a.mass_g * CP_AL
    tau = a.rsa * C
    if C:
        print(f'Sink capacity {C:.0f} J/K, tau = {tau:.0f} s')
    for P in a.power:
        tj_ss = a.ta + P * total
        line = f'{P:6.1f} W: steady Tj = {tj_ss:6.1f} C ({"OK" if tj_ss <= a.tj else "exceeds limit"})'
        if C:
            allowed = (a.tj - a.ta - P * path) / (P * a.rsa)
            if allowed >= 1:
                line += ', single shot: unlimited'
            elif allowed <= 0:
                line += ', single shot: not possible (path alone exceeds limit)'
            else:
                line += f', single shot to limit: {-tau * math.log(1 - allowed):.0f} s'
            line += f'; at sink cut-off {a.tsink_cut:.0f} C: Tj = {a.tsink_cut + P * path:.1f} C'
        print(line)
        if C and a.t_on > 0:
            T = a.ta
            first_start = first_cut = None
            tj_peak = 0.0
            for n in range(1, a.tests + 1):
                T = a.ta + (T - a.ta - P * a.rsa) * math.exp(-a.t_on / tau) + P * a.rsa
                tj_peak = max(tj_peak, T + P * path)
                if first_start is None and T >= a.tsink_start:
                    first_start = n
                if first_cut is None and T >= a.tsink_cut:
                    first_cut = n
                T = a.ta + (T - a.ta) * math.exp(-a.t_off / tau)
            avg = P * a.t_on / (a.t_on + a.t_off)
            print(f'    back-to-back {a.t_on:.0f} s on / {a.t_off:.0f} s off (mean {avg:.1f} W): '
                  f'sink reaches {a.tsink_start:.0f} C at test {first_start}, {a.tsink_cut:.0f} C at test {first_cut}, '
                  f'peak Tj {tj_peak:.1f} C, final sink {T:.1f} C')


if __name__ == '__main__':
    main()
