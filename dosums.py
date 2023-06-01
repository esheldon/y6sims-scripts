import numpy as np
import fitsio
import argparse
from esutil.numpy_util import between


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('fname')
    parser.add_argument('outfile')
    return parser.parse_args()


def get_data(fname):
    columns = [
        'mdet_step',
        'mask_flags',
        'gauss_flags',
        'gauss_psf_flags',
        'gauss_obj_flags',
        'psfrec_flags',
        'gauss_s2n',
        'gauss_T_ratio',
        'gauss_g_1',
        'gauss_g_2',
        'gauss_g_cov_1_1',
        'gauss_g_cov_2_2',
        'mfrac',
    ]
    data = fitsio.read(fname, columns=columns)

    ddict = {}
    for mdet_step in ['noshear', '1p', '1m']:
        wsel, = np.where(
            (data['mdet_step'] == mdet_step)
            & (data['gauss_flags'] == 0)
            # these should be redundant
            & (data['gauss_psf_flags'] == 0)
            & (data['gauss_obj_flags'] == 0)
            & (data['psfrec_flags'] == 0)
            & (data['mfrac'] < 0.02)
            & (data['mask_flags'] == 0)
            & ((data['mask_flags'] & (~16)) == 0)
            # & between(data['gauss_s2n'], 10, 100)
            & between(data['gauss_s2n'], 10, 1.e9)
            # & between(data['gauss_T_ratio'], 0.5, 2)
            & between(data['gauss_T_ratio'], 0.5, 1.e9)
        )
        ddict[mdet_step] = data[wsel]

    return ddict


def get_weights(data):
    return data['gauss_g_1'] * 0 + 1
    cov = 0.5 * (data['gauss_g_cov_1_1'] + data['gauss_g_cov_2_2'])
    return 1.0/(0.07**2 + cov)


def get_sums(data):
    weights = get_weights(data)
    wsum = weights.sum()

    out = np.zeros(
        1, dtype=[('wsum', 'f8'), ('e1sum', 'f8'), ('e2sum', 'f8')]
    )
    out['wsum'] = wsum
    out['e1sum'] = (data['gauss_g_1'] * weights).sum()
    out['e2sum'] = (data['gauss_g_2'] * weights).sum()
    return out


def main():
    args = get_args()
    ddict = get_data(args.fname)

    print(args.outfile)
    with fitsio.FITS(args.outfile, 'rw', clobber=True) as fits:
        for mdet_step in ddict:
            sums = get_sums(ddict[mdet_step])
            fits.write(sums, extname=mdet_step)


main()
