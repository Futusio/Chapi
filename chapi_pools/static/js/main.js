
// Below Code to dynamic search and it works!
$(document).on('keyup','#TakeMe', function(e) {
    if ($('#TakeMe').val().length != 0){
        $.ajax({
            method: 'POST',
            url: '/search',
            data: JSON.stringify({name:$('#TakeMe').val()}),
            success: function (response) {
                $('#results').html('')
                if(Object.keys(response).length != 0){
                    for(var key in response){
                        $('#results').append(`
                        <p id='result'><a class='chat_link' id='${response[key]}'>${response[key]}</a></p>
                        `)
                }} else {
                    $('#results').append("<p id='result'>No results</p>")
                }
            },
            error: function (e) {
                $('#results').append("<p id='result'>Error</p>")
            }
        })
        $('#results').fadeIn(500)
    } else {
        $('#results').fadeOut(500)
    }
})

// The method shows tips above the strings
$(document).on('click', '.chat_link', function() {
    // Step One: Check input-API field
    $('.chat_link').powerTip();
    const IDElem = this['id']
    if($('#user-token-input').val().length == 0){
        try {
            console.log('I am here')
            $(`#${IDElem}`).data('powertip', 'First you have to enter your token');
            $.powerTip.show($(`#${IDElem}`))
        } catch (error) {
            console.log('Was exception with: ', IDElem)
        }

    } else {
        $.ajax({
            method: 'POST',
            url: '/check_api',
            data: JSON.stringify({API:$('#user-token-input').val()}),
            success: function (response){
                if(response['status'] == 'success'){
                    $.ajax({
                        method: 'POST',
                        url: '/check_permission',
                        data: JSON.stringify({API:$('#user-token-input').val(), chat:IDElem}),
                        success: function (response) {
                            if(response['status'] == 'success'){
                                connection($('#user-token-input').val(), IDElem)
                            } else {
                                $(`#${IDElem}`).data('powertip', 'You do not have permission');
                                $.powerTip.show($(`#${IDElem}`))
                            }
                        },
                        error: function (e){
                            console.log('Error')
                        }
                    })

                } else {
                    $(`#${IDElem}`).data('powertip', 'The API does not exist');
                    $.powerTip.show($(`#${IDElem}`))
                }
            }, 
            error: function (e){
                console.log('Error')
            }
        })
    }
})


// Changy body? IDK How it works
function ChangeBody(){
    // The function Change Body beetwen API and CHAT
    if ($(".API").is(':visible')){ // To chat
        document.getElementById('API').style.cssText=`
            color: indianred;
            border: 2px solid indianred;
            background-color: white;
            `;
        hover(document.getElementById('API'))
        $(".API").fadeOut(300, function() {
            $('.messages').fadeIn(300, function() {
                var div = $(".scroll");
                div.scrollTop(div.prop('scrollHeight'))})
            $('.message_input').fadeIn(300)
        });
    } else{ // To documentation
        document.getElementById('API').style.cssText=`
            color: white;
            border: 2px solid #9A5A5A;
            background-color: #cd5c5c;
            `;
        $('.message_input').fadeOut(300)
        $('.messages').fadeOut(300, function(){
            $(".API").fadeIn(300, function() {
                var div = $(".scroll");
                div.scrollTop(0);
            });
        })
    }

}

function hover(element){

    element.onmouseover = function () {
        document.getElementById('API').style.cssText=`
            background-color: #cd5c5c;
            border: 2px solid #9A5A5A;
            color: #ffffff;
            `;
    };
    element.onmouseleave = function () {
        document.getElementById('API').style.cssText=`
            background-color: white;
            color: indianred;
            border: 2px solid indianred;
            `;
    }
}

// Pass to the main.js
function getApi(){
    $.ajax({
        method: 'POST',
        url: '/get_api',
        data: JSON.stringify({login:$('#pop-input').val()}),
        success: function (response) {
            console.log(`${response['status']} + ${response['token']}`)
            if(response['status'] == 'success'){
                alert(`Your own API-Token is: \n${response['token']}\nSave it`)
                $("#user-token-input").val(response['token'])
            } else {
                alert("Error: The login is busy")
            }
            // var json = jQuery.parseJSON(response)
        },
        error: function (e) {
            alert('Oops... Seems like something went wrong')
        }
    })
}