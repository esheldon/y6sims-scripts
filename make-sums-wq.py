import os


TEMPLATE = r"""
command: |
    source activate y6sims

    export OMP_NUM_THREADS=1

    python $HOME/y6-sims/mysims/dosums.py %(fname)s %(outfile)s

job_name: %(job_name)s
"""


def get_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('flist')
    return parser.parse_args()


def main():

    args = get_args()

    wqdir = os.path.join(
        os.path.dirname(args.flist),
        'sums',
    )

    if not os.path.exists(wqdir):
        os.makedirs(wqdir)

    with open(args.flist) as fobj:
        fnames = [f.strip() for f in fobj]

    for i, fname in enumerate(fnames):

        bname = os.path.basename(fname)
        # tilename
        tilename = bname[:12]
        job_name = [tilename]

        if 'plus' in fname:
            job_name += ['plus']
        else:
            job_name += ['minus']

        job_name += ['sums']
        job_name = '-'.join(job_name)

        wqfile = os.path.join(wqdir, job_name+'.yaml')
        outfile = job_name+'.fits'

        # wqfile = f'wq/sums-{i:03d}.yaml'

        text = TEMPLATE % {
            'fname': fname,
            'job_name': job_name,
            'outfile': outfile,
        }

        print('writing:', wqfile)
        with open(wqfile, 'w') as fobj:
            fobj.write(text)


main()
