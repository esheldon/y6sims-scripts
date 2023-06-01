import numpy as np
import os
import fitsio
import argparse
import esutil as eu
# from tqdm import trange


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('flist', nargs='+')
    return parser.parse_args()


def get_summed(ddict):

    summed = {}
    for mdet_type, data in ddict.items():
        # print(mdet_type, data)
        sdata = data[0].copy()

        for n in sdata.dtype.names:
            sdata[n] = data[n].sum()

        summed[mdet_type] = sdata

    return summed


def get_shear(data):
    dns = data['noshear']
    d1p = data['1p']
    d1m = data['1m']

    g1 = dns['e1sum'] / dns['wsum']
    g2 = dns['e2sum'] / dns['wsum']

    g1_1p = d1p['e1sum'] / d1p['wsum']
    g1_1m = d1m['e1sum'] / d1m['wsum']

    R = (g1_1p - g1_1m) / 0.02

    s1 = g1 / R
    s2 = g2 / R
    return s1, s2, R


def get_m1_c1(plus, minus):

    s1_1p, s2_1p, R_1p = get_shear(plus)
    s1_1m, s2_1m, R_1m = get_shear(minus)

    R11 = 0.5*(R_1p + R_1m)  # noqa
    m1 = (s1_1p - s1_1m)/0.04 - 1
    c1 = (s1_1p + s1_1m)/2
    c2 = (s2_1p + s2_1m)/2
    return m1, c1, c2, R11


def sub1(summed, data, index):

    new = {}
    for mdet_type in summed:
        summed_data = summed[mdet_type]
        tosub = data[mdet_type][index]

        tmp = summed_data.copy()

        for n in tmp.dtype.names:
            tmp[n] -= tosub[n]

        new[mdet_type] = tmp

    return new


def jackknife(plus, minus):
    n = plus['noshear'].size

    plus_summed = get_summed(plus)
    minus_summed = get_summed(minus)

    m1, c1, c2, R = get_m1_c1(plus_summed, minus_summed)

    m1vals = np.zeros(plus['noshear'].size)
    c1vals = m1vals.copy()
    c2vals = m1vals.copy()
    Rvals = np.zeros(n)

    for i in range(n):
        tplus_summed = sub1(plus_summed, plus, i)
        tminus_summed = sub1(minus_summed, minus, i)

        tm1, tc1, tc2, tR = get_m1_c1(tplus_summed, tminus_summed)

        m1vals[i] = tm1
        c1vals[i] = tc1
        c2vals[i] = tc2
        Rvals[i] = tR

    fac = (n - 1) / n
    m1cov = fac * ((m1 - m1vals)**2).sum()
    c1cov = fac * ((c1 - c1vals)**2).sum()
    c2cov = fac * ((c2 - c2vals)**2).sum()
    Rcov = fac * ((R - Rvals)**2).sum()

    return {
        'R': R,
        'Rerr': np.sqrt(Rcov),
        'm1': m1,
        'm1err': np.sqrt(m1cov),
        'c1': c1,
        'c1err': np.sqrt(c1cov),
        'c2': c2,
        'c2err': np.sqrt(c2cov),
    }


def printrange(res, name):
    low = res[name] - 3 * res[name+'err']
    high = res[name] + 3 * res[name+'err']

    print(f'{low:.3g} < {name} < {high:.3g} (99.7%)')


def printres(res):

    print('R: %.3g +/- %.3g (99.7%%)' % (res['R'], res['Rerr'] * 3))
    print('m1: %.3g +/- %.3g (99.7%%)' % (res['m1'], res['m1err'] * 3))
    print('c1: %.3g +/- %.3g (99.7%%)' % (res['c1'], res['c1err'] * 3))
    print('c2: %.3g +/- %.3g (99.7%%)' % (res['c2'], res['c2err'] * 3))

    print()
    printrange(res, 'R')
    printrange(res, 'm1')
    printrange(res, 'c1')
    printrange(res, 'c2')


def main():
    args = get_args()

    plus = {
        'noshear': [],
        '1p': [],
        '1m': [],
    }
    minus = {
        'noshear': [],
        '1p': [],
        '1m': [],
    }
    for fname in args.flist:
        if 'plus' in fname:
            # we don't do plus independently, instead we always pair
            continue

        minus_fname = fname
        plus_fname = fname.replace('minus', 'plus')
        assert minus_fname != plus_fname

        if not os.path.exists(plus_fname):
            continue

        print(minus_fname)
        print('    ', plus_fname)

        with fitsio.FITS(minus_fname) as fobj:
            for mdet_step in plus:
                data = fobj[mdet_step][:]
                minus[mdet_step].append(data)

        with fitsio.FITS(plus_fname) as fobj:
            for mdet_step in plus:
                data = fobj[mdet_step][:]
                plus[mdet_step].append(data)

    for mdet_step in plus:
        plus[mdet_step] = eu.numpy_util.combine_arrlist(plus[mdet_step])
        minus[mdet_step] = eu.numpy_util.combine_arrlist(minus[mdet_step])

    res = jackknife(plus=plus, minus=minus)
    printres(res)


main()
