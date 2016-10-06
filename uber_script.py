#!/usr/bin/env python
"""
Usage:
    python uber_script.py [<num_jobs>]
"""
import os, sys

num_jobs = 1
if len(sys.argv) == 2:
    if sys.argv.isdigit():
        num_jobs = sys.argv[1]
    else:
        raise ValueError('Argument to this script must be an integer.')
if len(sys.argv) > 2:
    raise ValueError('Usage: python uber_script.py [<num_jobs>]')

# prepare the data
os.system('python data_prep.py')
os.system('utils/fix_data_dir.sh data/train_yesno/')
os.system('utils/fix_data_dir.sh data/test_yesno/')

# language model
cmd = 'utils/prepare_lang.sh ' + \
      '--position-dependent-phones false ' + \
      'dict "<SIL>" dict/temp data/lang'
os.system(cmd)
os.system('lm/prepare_lm.sh')

# train
cmd = 'steps/make_mfcc.sh --nj ' + num_jobs + \
      ' data/train_yesno exp/make_mfcc/train_yesno'
os.system(cmd)
cmd = 'steps/compute_cmvn_stats.sh data/train_yesno exp/make_mfcc/train_yesno'
os.system(cmd)
cmd = 'steps/train_mono.sh --nj ' + num_jobs + \
      ' --cmd utils/run.pl data/train_yesno data/lang exp/mono'
os.system(cmd)

# test
cmd = 'steps/make_mfcc.sh --nj ' + num_jobs + \
      ' data/test_yesno exp/make_mfcc/test_yesno'
os.system(cmd)
cmd = 'steps/compute_cmvn_stats.sh data/test_yesno exp/make_mfcc/test_yesno'
os.system(cmd)

# make graphs
cmd = 'utils/mkgraph.sh --mono data/lang_test_tg exp/mono exp/mono/graph_tgpr'
os.system(cmd)
cmd = 'steps/decode.sh --nj ' + num_jobs + \
      ' exp/mono/graph_tgpr data/test_yesno exp/mono/decode_test_yesno'

# evaluate
cmd = 'steps/get_ctm.sh data data/lang_test_tg exp/mono/decode_test_yesno'
os.system(cmd)
