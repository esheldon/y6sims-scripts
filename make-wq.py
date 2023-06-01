import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--seed', type=int, required=True)
    return parser.parse_args()


def get_tiles():
    import glob
    import os

    tdir = '/gpfs02/astro/workarea/beckermr/MEDS_DIR/des-pizza-slices-y6-v15-nostars/'  # noqa
    pattern = os.path.join(tdir, 'DES*')
    dlist = glob.glob(pattern)
    tilenames = [os.path.basename(d) for d in dlist]
    return tilenames


def read_config(args):
    import yaml
    with open(args.config) as fobj:
        conf = yaml.safe_load(fobj)

    return conf


def copy_files(args, outdir):
    import shutil
    conf = read_config(args)

    print(f'copying {args.config} -> {outdir}/')
    shutil.copy(args.config, outdir+'/')

    if 'config_file' in conf['pizza_cutter']:
        pzconf = conf['pizza_cutter']['config_file']
        print(f'copying {pzconf} -> {outdir}/')
        shutil.copy(pzconf, outdir+'/')

    if 'config_file' in conf['metadetect']:
        mdconf = conf['metadetect']['config_file']
        print(f'copying {mdconf} -> {outdir}/')
        shutil.copy(mdconf, outdir+'/')


def main(args):
    import os
    import random

    random.seed(args.seed)

    tilenames = get_tiles()
    print('found:', len(tilenames), 'tiles')
    outdir = f'runs/{args.run}'
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    copy_files(args, outdir)

    for tilename in tilenames:
        seed = random.randint(0, 2**16)

        job_name = f'{args.run}-{tilename}'
        fname = os.path.join(
            outdir,
            f'{job_name}.yaml'
        )
        text = TEMPLATE % {
            'tilename': tilename,
            'config': os.path.basename(args.config),
            'seed': seed,
            'job_name': job_name,
        }
        print(fname)
        with open(fname, 'w') as fobj:
            fobj.write(text)


TEMPLATE = r"""
command: |
    source activate y6sims

    tilename=%(tilename)s
    config=%(config)s
    seed=%(seed)d

    nproc=$(cat /proc/cpuinfo | grep "^processor" | wc -l)

    echo "nproc: $nproc"

    export MEDS_DIR=/gpfs02/astro/workarea/beckermr/MEDS_DIR/
    export OMP_NUM_THREADS=1

    export IMSIM_DATA=${MEDS_DIR}
    export TMPDIR=/data/esheldon/tmp

    plusdir="./${tilename}-plus"
    minusdir="./${tilename}-minus"

    mkdir -p ${plusdir}
    mkdir -p ${minusdir}

    run-eastlake-sim \
      -v 1 \
      --seed ${seed} \
      ${config} \
      ${plusdir} \
      stamp.shear.g1=0.02 \
      stamp.shear.g2=0.0 \
      metadetect.n_jobs=${nproc} \
      output.nproc=${nproc} \
      output.tilename=${tilename}

    run-eastlake-sim \
      -v 1 \
      --seed ${seed} \
      ${config} \
      ${minusdir} \
      stamp.shear.g1=-0.02 \
      stamp.shear.g2=0.0 \
      metadetect.n_jobs=${nproc} \
      output.nproc=${nproc} \
      output.tilename=${tilename}

job_name: %(job_name)s
mode: bynode
"""

if __name__ == '__main__':
    args = get_args()
    main(args)
