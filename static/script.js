// home.html
$(document).ready(function(){
    if($('.home').length>0) {
        function load_feed(next_cursor){
            var content = $('#content');
            var tag = content.data('tag');
            var cursor = content.data('cursor');
            var fl = $('#feed_list');
            $.ajax({
                url:'/feeddata/'+tag+'/', 
                dataType:'json',
                type:'post',
                data:{'cursor':(cursor ? cursor : '' )},
                success:function(result){
                    var row_str = '';
                    for(var i = 0 ; i < result.feeds.length ; i++){
                        var feeds = result.feeds;
                        fp = feeds[i]['full_picture'] ? '<img src="'+feeds[i]['full_picture']+'" />' : ''
                        row_str +=    '<tr><td>'+feeds[i]['message']+fp+'</td></tr>';
                    }
                    fl.append(row_str)
                    if(!result.more)
                        $('#next_btn').prop('disabled', true);
                    content.data('cursor', result.cursor);
                }
            })
        }
        $('#next_btn').click(function(){
            load_feed($('#content').data('cursor'));
        })
        load_feed();    
    } else if($('.admin').length>0){
        $('#login_btn').click(function(){
            location.href = '/admin/login'
        })
        $('#reset_btn').click(function(){
            if(confirm('정말 삭제 합니까? 모든 정보가 삭제 됩니다.')){
                $.ajax({
                    url:'/admin/reset'
                })
            }
        })
    }
})