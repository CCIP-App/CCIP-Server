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
#Source file:
#
#(function(){
#	keys = {
#		'type': {'type': 'null'},
#		'token': {'type': 'qrcode'},
#		'id': {'type': 'field', 'value': '暱稱'},
#		'飲食': {'type': 'field', 'value': '飲食習慣'},
#		'個人贊助': {'type': 'value', 'value': 'Y'},
#		'price': {'type': 'price'},
#		'shirt_size': {'type': 'field', 'value': '回饋贈品衣服尺寸'}
#	};
#
#	function keys_by_type(type){
#		field = {};
#		for (k in keys){
#			if (keys[k].type == type){
#				field[k] = keys[k];
#			}
#		}
#		return field;
#	}
#
#	output = {};
#
#	// Field type
#	a = document.getElementsByClassName('control-group');
#	a = Array.prototype.filter.call(a, b => b.classList.length == 2);
#	a = Array.prototype.filter.call(a, b => b.getElementsByClassName('control-label')[0].innerText.match(/^\n/) == null);
#	ks = keys_by_type('field');
#	for (b of a){
#		for (k in ks){
#			if (b.getElementsByClassName('control-label')[0].innerText == ks[k].value){
#				output[k] = b.getElementsByClassName('controls')[0].innerText;
#			}
#		}
#	}
#
#	// Price type
#	ks = keys_by_type('price');
#	for (k in ks){
#		output[k] = document.getElementsByClassName('currency-value')[document.getElementsByClassName('currency-value').length-1].innerText.replace(',','');
#	}
#
#	// QRCode type
#	qrid = '';
#	for (i of document.getElementsByTagName('img')){
#		if (i.currentSrc.match(/^https:\/\/kktix\.com\/g\/qr/)){
#			qrid = i.currentSrc.split('=').pop();
#		}
#	}
#	ks = keys_by_type('qrcode');
#	for (k in ks){
#		output[k] = qrid;
#	}
#
#	// value type
#	ks = keys_by_type('value');
#	for (k in ks){
#		output[k] = ks[k].value;
#	}
#
#	// null type
#	ks = keys_by_type('null');
#	for (k in ks){
#		output[k] = '';
#	}
#
#	function convert2csvla(data){
#		output = '';
#		for (i in data){
#			output += i + ',';
#		}
#		output = output.slice(0, -1) + '\n';
#		for (i in data){
#			output += data[i] + ',';
#		}
#		output = output.slice(0, -1);
#		return output;
#	}
#
#	url = 'http://$server:$port/$token/' + convert2csvla(output).replace('\n','😱');
#	window.open(url);
#})()

# By Minifer https://javascript-minifier.com/
    echo "javascript:!function(){function e(e){for(k in field={},keys)keys[k].type==e&&(field[k]=keys[k]);return field}for(b of(keys={type:{type:'null'},token:{type:'qrcode'},id:{type:'field',value:'暱稱'},'飲食':{type:'field',value:'飲食習慣'},'個人贊助':{type:'value',value:'Y'},price:{type:'price'},shirt_size:{type:'field',value:'回饋贈品衣服尺寸'}},output={},a=document.getElementsByClassName('control-group'),a=Array.prototype.filter.call(a,e=>2==e.classList.length),a=Array.prototype.filter.call(a,e=>null==e.getElementsByClassName('control-label')[0].innerText.match(/^\n/)),ks=e('field'),a))for(k in ks)b.getElementsByClassName('control-label')[0].innerText==ks[k].value&&(output[k]=b.getElementsByClassName('controls')[0].innerText);for(k in ks=e('price'),ks)output[k]=document.getElementsByClassName('currency-value')[document.getElementsByClassName('currency-value').length-1].innerText.replace(',','');for(i of(qrid='',document.getElementsByTagName('img')))i.currentSrc.match(/^https:\/\/kktix\.com\/g\/qr/)&&(qrid=i.currentSrc.split('=').pop());for(k in ks=e('qrcode'),ks)output[k]=qrid;for(k in ks=e('value'),ks)output[k]=ks[k].value;for(k in ks=e('null'),ks)output[k]='';url='http://$server:$port/$token/'+function(e){for(i in output='',e)output+=i+',';for(i in output=output.slice(0,-1)+'\n',e)output+=e[i]+',';return output=output.slice(0,-1),output}(output).replace('\n','😱'),window.open(url)}();"
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
    req=$(urldecode $(echo -e 'HTTP/1.1 200 OK\r\n\r\n<script>window.close()</script>' | nc -l $port | head -n1 | $gnu_grep -oP '/\K.*\ ')) # Must be GNU Grep
    req_token=$(echo $req | $gnu_grep -oP '\K.*(?=/)' )
    req_data=$(echo $req | $gnu_grep -oP '/\K.*')
    if [ "$req_token" == "$token" ]
    then
        [ -n "$req" ] && echo $req_data | sed 's/😱/\n/g' > /tmp/attendee_$$.csv && cat /tmp/attendee_$$.csv && python import.py /tmp/attendee_$$.csv scenario-attendee.json
    else
        echo wrong_token
    fi
done
