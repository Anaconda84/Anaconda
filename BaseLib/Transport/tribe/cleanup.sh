cd `dirname 0`/tribe
find tribler/ -name \*.pyc -exec rm \{\} \;

for dir in tribler/Tribler/Tests \
  tribler/Tribler/Main/vwxGUI \
  tribler/Tribler/Main/Build \
  tribler/Tribler/Video/Images \
  tribler/clean.bat \
  tribler/makedist.bat \
  tribler/playmakedist.bat \
  tribler/pluginmakedist.bat \
  tribler/pluginmakedist_FX_only.bat \
  tribler/pluginmakedist_IE_only.bat \
  tribler/reset-keepid.bat \
  tribler/reset.bat \
  tribler/runmac.command \
  tribler/vlc4plugin-1.0.1-r13995.patch \
  tribler/Tribler/Images/*.png \
  tribler/Tribler/Web2/ \
  tribler/Tribler/Plugin/Build/ \
  tribler/Tribler/Test/ \
  tribler/Tribler/Core/DecentralizedTracking/kadtracker/test_*.py \
  tribler/Tribler/Core/DecentralizedTracking/kadtracker/test_logs \
  tribler/Tribler/Plugin/BackgroundProcess-njaal.py \
  tribler/Tribler/Player/swarmplayer-njaal.py \
  tribler/Tribler/Tools/createlivestream-njaal.py \
  tribler/Tribler/Player/Build/; do
test -e $dir && rm -r $dir
done

sed -i "s/DEBUG = True/DEBUG = False/g" tribler/Tribler/*/*.py
sed -i "s/DEBUG = True/DEBUG = False/g" tribler/Tribler/*/*/*.py

