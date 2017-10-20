#!/bin/bash
echo "set title 'Time to add a new newspaper depending of the number of already added newspaper'
set ylabel 'Merge time'
set xlabel 'Number of LA newspaper'
set key left box
set term png
set datafile separator \",\"
set output 'graphMergeTime.png'
set style data linespoints
plot 'out.csv' using 1:3 title 'merge file'" | gnuplot


echo "set title 'Size of the merge file depending of the number of already added newspaper'
set ylabel 'File size (ko)'
set xlabel 'Number of LA newspaper'
set key left box
set term png
set datafile separator \",\"
set output 'graphMergeSize.png'
set style data linespoints
plot 'out.csv' using 1:6 title 'merge file', 'out.csv' using 1:7 title 'newspaper file'" | gnuplot

echo "set title 'Time of merge depending of the size of the merged file'
set xlabel 'File size (ko)'
set ylabel 'Time (s)'
set key left box
set term png
set datafile separator \",\"
set output 'graphMergeSizeTime.png'
set style data points
plot 'out.csv' using 6:3 title 'merge file'" | gnuplot
