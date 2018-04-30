#! /bin/bash -ex

# Use -gt 1 to consume two arguments per pass in the loop (e.g. each
# argument has a corresponding value to go with it).
# Use -gt 0 to consume one or more arguments per pass in the loop (e.g.
# some arguments don't have a corresponding value to go with it such
# as in the --default example).
while [[ $# -gt 0 ]]
do
key=$1
case $key in
    -s|--start)
    option="start"
    ;;
    -q|--stop)
    option="stop"
    ;;
    *)  # unknown option
    ;;
esac
shift
done

echo "option is $option"
hosts=("cloudlet026.maas" "cloudlet027.maas" "cloudlet028.maas" "cloudlet029.maas" "cloudlet030.maas")

if [[ "${option}" == "start" ]]; then
    for host in "${hosts[@]}"
    do
        printf "port forwarding for ${host}"
        ssh -f -N -L 600${host:10:1}:localhost:6006 ${host}
        ssh -f -N -L 555${host:10:1}:localhost:5555 ${host}
    done
fi

if [[ "${option}" == "stop" ]]; then
    pgrep -f "ssh -f -N -L" | xargs -I {} kill {}
fi

