export FOGLAMP_ROOT=/home/pi/FogLAMP/
#export FOGLAMP_DATA=/mnt/ram-disk/data/
export FOGLAMP_DATA=$FOGLAMP_ROOT/data
$FOGLAMP_ROOT/scripts/foglamp kill &> /dev/null
sudo logrotate -f /etc/logrotate.d/rsyslog
for size in 30000 15000 5000 500 100 50; do
        for threads in 1 ; do
                buffersize=$(($size * $threads))
                d="result_${size}_${threads}_${buffersize}"
                mkdir $d
                echo $size $threads $buffersize >> $d/out.txt
                cp ingest.py python/foglamp/services/south/ingest.py
                sed -i "s/_readings_buffer_sizeVAR/$buffersize/g" python/foglamp/services/south/ingest.py
                sed -i "s/_readings_insert_batch_sizeVAR/$size/g" python/foglamp/services/south/ingest.py
                sed -i "s/_max_concurrent_readings_insertsVAR/$threads/g" python/foglamp/services/south/ingest.py
                sed -n -e 101p python/foglamp/services/south/ingest.py >> $d/out.txt
                sed -n -e 104p python/foglamp/services/south/ingest.py >> $d/out.txt
                sed -n -e 107p python/foglamp/services/south/ingest.py >> $d/out.txt
                echo YES | $FOGLAMP_ROOT/scripts/foglamp reset &> /dev/null
                sudo logrotate -f /etc/logrotate.d/rsyslog
                $FOGLAMP_ROOT/scripts/foglamp start &> /dev/null
                sleep 300
                $FOGLAMP_ROOT/scripts/foglamp kill &> /dev/null
                sleep 15
                sqlite3 $FOGLAMP_DATA/foglamp.db 'select * from statistics' >> $d/out.txt
                cp /var/log/syslog $d/syslog
        done
done

