#/bin/bash

if [[ "$1" =~ ".seq" ]]; then 
  echo ------ doing: $0 $1
else
  echo do: $0 _FILE_NAME_.seq
  break
fi

#Emissivity=0.95
#while read cfg_name cfg_val; do
#  
#
#done < config




binarydir=fout
rm -rf $binarydir
mkdir -p $binarydir

echo '------ converting seq to binary ------ ' 
#
# read the sequence file
# produce the binary files frame by frame as seq_n*.fff
#

./share/seqtobinary.pl $1 $binarydir
echo ''

txtoutdir=tout
rm -rf $txtoutdir
mkdir -p $txtoutdir
echo '------ converting binary to text ----- '
./share/binarytotext.sh $binarydir $txtoutdir
echo ''

nfile=`ls -l $binarydir/*_*.* | wc -l`
echo '------ converting text to root ----- '
echo '    found number of files: '$nfile''
outdir=roo
rm -rf $outdir
mkdir -p $outdir
if (( nfile <= 0 )); then
  echo 'number of files '$nfile' <= 0 '
  break
fi
./share/texttoroot.py $outdir $nfile
echo ''

echo 'clear binary folder: '$binarydir''
rm -rf $binarydir
echo 'clear text out folder: '$txtoutdir''
rm -rf $txtoutdir

mv config $outdir
ls -l $outdir/config

echo 'root results in folder: '$outdir''
echo ''
echo 'All done!'

