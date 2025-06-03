#!/bin/bash

BLOCK_SIZES=("4k" "8k" "16k" "32k" "64k" "128k")
NUMJOBS=("1" "2" "3" "4")
PATTERNS=("seq_read" "seq_write" "rand_read" "rand_write")

C_DEV="/dev/nullb0"
RUST_DEV="/dev/nullb1"

declare -A SCHED_MAP=( ["results_none"]="none" ["results_mq"]="mq-deadline" )

sudo modprobe null_blk queue_mode=2 irqmode=0 \
	hw_queue_depth=256 memory_backed=1 bs=4096 \
	completion_nsec=0 no_sched=1 gb=16 nr_devices=2
sudo modprobe rnull_mod || sudo insmod drivers/block/rnull.ko memory_backed=1

ls /dev/nullb*

for sched_dir in "results_none" "results_mq"; do
	SCHED=${SCHED_MAP[$sched_dir]}
	base_path="$HOME/$sched_dir"

	for pattern in "${PATTERNS[@]}"; do
		case $pattern in
			seq_read) RW=read ;;
			seq_write) RW=write ;;
			rand_read) RW=randread ;;
			rand_write) RW=randwrite ;;
		esac

		for bs in "${BLOCK_SIZES[@]}"; do
			for nj in "${NUMJOBS[@]}"; do
				dir_path="$base_path/$pattern"
				mkdir -p "$dir_path"

				C_OUT="$dir_path/c_bs${bs}_jobs${nj}.json"
				RUST_OUT="$dir_path/rust_bs${bs}_jobs${nj}.json"

				echo " C: $pattern bs=$bs jobs=$nj sched=$SCHED"
				sudo fio --filename=$C_DEV --iodepth=64 --ioengine=psync --direct=1 \
					--rw=$RW --bs $bs --size=1G --time_base --runtime=30 --numjobs=$nj \
					--group_reporting --output-format=json --output=$C_OUT \
					--name=c_test --ioscheduler=$SCHED > /dev/null
				
				echo " Rust: $pattern bs=$bs jobs=$nj sched=$SCHED"
				sudo fio --filename=$RUST_DEV --iodepth=64 --ioengine=psync --direct=1 \
					--rw=$RW --bs $bs --size=1G --time_base --runtime=30 --numjobs=$nj \
					--group_reporting --output-format=json --output=$RUST_OUT \
					--name=c_test --ioscheduler=$SCHED > /dev/null
			done
		done
	done
done
