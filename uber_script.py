#!/usr/bin/env python
"""
Usage:
    python uber_script.py [<num_jobs>]

NOTE: Default value for <num_jobs> if not given is 1.

NOTE: I decided to hardcode the paths because many of these scripts had
hardcoded them and it would break too much to give user the leeway to decide
where things go. For example, the data_prep.py script assumes the data
directories to be in data/train_yesno and data/test_yesno. For consistency, I am
not allowing the user to control these.
    If this were a simple input and output path situation, asking for user input
might be better, but in this case I think it's better not to give the user the
choice of where these go.
"""
import os, sys

num_jobs = '1'
if len(sys.argv) == 2:
    if sys.argv[1].isdigit():
        num_jobs = sys.argv[1]
    else:
        raise ValueError('Argument to this script must be an integer.')
if len(sys.argv) > 2:
    message = 'Usage: python uber_script.py [<num_jobs>]\n'
    message += '   EG: python uber_script.py 4'
    raise ValueError(message)

# create data directory and subdirs
os.system('mkdir data')
os.system('mkdir data/train_yesno')
os.system('mkdir data/test_yesno')

# prepare the data
os.system('python data_prep.py')
os.system('utils/utt2spk_to_spk2utt.pl data/train_yesno/utt2spk > data/train_yesno/spk2utt')
os.system('utils/utt2spk_to_spk2utt.pl data/test_yesno/utt2spk > data/test_yesno/spk2utt')
os.system('utils/fix_data_dir.sh data/train_yesno/')
os.system('utils/fix_data_dir.sh data/test_yesno/')

# create dict directory and contents
os.system('mkdir dict')
os.system('echo -e "K\nEH\nN\nL\nOW" > dict/phones.txt')
os.system('echo -e "YES K EH N\nNO L OW" > dict/lexicon.txt')
os.system('echo "SIL" > dict/silence_phones.txt')
os.system('echo "SIL" > dict/optional_silence.txt')
os.system('mv dict/phones.txt dict/nonsilence_phones.txt')
os.system('cp dict/lexicon.txt dict/lexicon_words.txt')
os.system('echo "<SIL> SIL" >> dict/lexicon.txt')

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

# print to screen human-readable top 20 results of lattice
cmd = "$KALDI_ROOT/src/fstbin/fstcopy " + \
      "'ark:gunzip -c exp/mono/fsts.1.gz|' " + \
      "ark,t:- | head -n 20"
os.system('source ./path.sh\n' + cmd)  # kaldi path as set in path.sh
