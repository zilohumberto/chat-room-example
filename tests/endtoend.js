var ws = new WebSocket("ws://0.0.0.0:8500/websocket")



function executeAction(actionBody){
    let response;
    console.log("ActionBody:", actionBody)
    //console.log('Action:', actionBody.action);
    if (actionBody.action == 'get_rooms'){
        return {
            'action': 'join_room',
            'params': {
                'room': actionBody.params.rooms[0]
            }
        }
    }else{
        return null;
    }
    
}


ws.onopen = function(evt){
    get_room = {
        'action': 'get_rooms',
        'params':{

        }
    }
    ws.send(JSON.stringify(get_room))
}


ws.onmessage = function(evt){
    try{
        let data = JSON.parse(evt.data);
        response = executeAction(data);
        if (response != null){
            console.log('Sending response through WS')
            ws.send(JSON.stringify({action: response.action, params: response.params}));
        }
    }catch{
        console.log(evt.data)
        return null;
    }
    
}

