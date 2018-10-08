#!/bin/bash

token='I_am_the_token'
server='[server]'
port='8000'
gnu_grep='grep'
md5_cmd='md5sum'
#gnu_grep='ggrep'
#md5_cmd='md5'

# Active env
# source ../env/bin/activate

print_js(){
    name_field='1'
    token_field='6'
    meal_field='9'
    echo "javascript:
            (function(){
                a = document.getElementsByClassName('controls');
                b = a[$name_field].firstElementChild.src.split('=')[2];
                c = a[$token_field].firstElementChild.textContent.trim();
                d = a[$meal_field].firstElementChild.textContent.trim().substr(0,1);
                url = 'http://$server:$port/$token/'+c+','+b+','+d+',';
                window.open(url);
            })()" | tr -d '\n' | sed 's/\ //g'
    echo
}

print_instruction(){
    echo "1. Copy the following code to a new bookmark"
    echo "2. Enter the detail of the ticket"
    echo "3. Click the bookmark"
    echo
    echo "===================code==================="
    print_js
    echo "===================code==================="
}


urldecode(){
    [ -n "$1" ] && python2 -c "import sys, urllib as ul; print ul.unquote_plus(sys.argv[1])" $1
}

token=$(echo $token | $md5_cmd | awk '{print $1}')
print_instruction

while true
do
    req=$(urldecode $(echo -e 'HTTP/1.1 200 OK\r\n\r\n<script>window.close()</script>' | nc -l $port | head -n1 | $gnu_grep -oP '/\K.*,.*,.*\ ')) # Must be GNU Grep
    req_token=$(echo $req | $gnu_grep -oP '\K.*(?=/)' )
    req_data=$(echo $req | $gnu_grep -oP '/\K.*,.*,.*')
    if [ "$req_token" == "$token" ]
    then
        [ -n "$req" ] && echo 'id,token,飲食,個人贊助' > /tmp/attendee_$$.csv && echo $req_data >> /tmp/attendee_$$.csv && python import.py /tmp/attendee_$$.csv scenario-attendee.json
    else
        echo wrong_token
    fi
done
