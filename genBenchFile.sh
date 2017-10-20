#!/bin/bash

END=150
inFilePath="benchmerge.log"
outFilePath="out.csv"
MergeFilePrefix="mergedfile"
NonMergeFilePrefix="docfile"

echo "" > $outFilePath

for i in $(seq 1 $END); do
	line=$(sed "${i}q;d" $inFilePath)
	mergesize=$(stat --printf="%s" "$MergeFilePrefix$i")
	filesize=$(stat --printf="%s" "$NonMergeFilePrefix$i")
	echo "$i,$line,$((mergesize/1024)),$((filesize/1024))" >> $outFilePath
done
