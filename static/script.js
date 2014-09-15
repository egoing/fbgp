// Library


function escapeHtml(string) {
    var entityMap = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': '&quot;', "'": '&#39;', "/": '&#x2F;'};
    return String(string).replace(/[&<>"'\/]/g, function (s) {
      return entityMap[s];
  });
}

function nl2br(string){
    return String(string).replace(/\n/g, '<br/>')
}

function space2br(string){
    return String(string).replace(/ /g, '&nbsp;')
}

function message(string){
    var t = Math.random();
    var string  = escapeHtml(string);
    string = nl2br(string);
    string = space2br(string);
    return string
}


// home.html
$(document).ready(function(){
    if($('.home').length>0) {
        function load_feed(next_cursor){
            var content = $('#content');
            var tag = content.data('tag');
            var cursor = content.data('cursor');
            var fl = $('#feed_list');
            $.ajax({
                url:'/feeddata/'+tag, 
                dataType:'json',
                type:'get',
                data:{'cursor':(cursor ? cursor : '' )},
                success:function(result){
                    $('#next_btn').show().blur();
                    var row_str = '';
                    var row = [];
                    for(var i = 0 ; i < result.feeds.length ; i++){
                        var feed = result.feeds[i];
                        row_str +=  '<li class="entry" data-post_key="'+feed['key_urlsafe']+'">'
                        row_str += '<div class="message">';
                        row_str += feed['full_picture'] ? '<div class="picture"><img src="'+feed['full_picture']+'" /></div>' : '';
                        row_str += message(feed['message']);
                        row_str += '<ul class="meta">'
                        row_str += '<li><a href="/member/post?member='+feed['member']['key_urlsafe']+'">'+feed['member']['name']+'</a></li>';
                        row_str += '<li><a href="/post/'+feed['key_urlsafe']+'">'+feed['created_time']+'</a></li>';
                        row_str += '<li><a href="" class="comment_btn">댓글보기</a></li>';
                        row_str += '</ul></div>';
                        row_str += '<div class="comment"><ul class="comment_data"></ul><button class="comment_more_btn btn btn-default btn-sm">더보기</button></div>';
                        row_str += '</li>';
                    }
                    fl.append($(row_str))
                    if(!result.more)
                        $('#next_btn').prop('disabled', true);
                    fl.autolink();
                    content.data('cursor', result.cursor);
                }
            })
        }
        $('#next_btn').click(function(){
            load_feed($('#content').data('cursor'));
        })
        load_feed();    
        $('body').on('click', '.comment_btn, .comment_more_btn', function(){
            $this = $(this)
            $entry = $this.parents('.entry');
            $comment = $entry.find('.comment')
            $more = $entry.find('.comment_more_btn')
            $data = $entry.find('.comment_data')
            $this.blur()
            $.ajax({
                url:/commentdata/+$entry.data('post_key'),
                dataType:'json',
                type:'get',
                data:{next_cursor:$comment.data('next_cursor')},
                success:function(result){
                    if(Math.max($data.find('li').length, result.entries.length)>0){
                        $comment.show();
                    }
                    str = ''
                    for(var i=0; i<result.entries.length; i++){
                        str += '<li>'
                        str += result.entries[i].message
                        str += '<div class="meta">'
                        str += '<span class="name"><a href="/member/comment?member='+result.entries[i].member.key_urlsafe+'">'+result.entries[i].member.name+'</a></span> | '
                        str += '<span class="date">'+result.entries[i].created_time+'</span></li>'    
                        str += '</div>'
                    }
                    if(result.next_cursor && result.more) {$more.show() } else {$more.hide() }
                    $comment.data('next_cursor', result.next_cursor)
                    $data.append(str)
                    $data.autolink();
                }
            })
            return false;  
        })
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


jQuery.fn.autolink = function (target) {
    if (target == null) target = '_parent';
    return this.each( function(){
        var re = /((http|https|ftp):\/\/[\w?=&.\/-;#~%-]+(?![\w\s?&.\/;#~%"=-]*>))/g;
        $(this).html( $(this).html().replace(re, '<a href="$1" target="'+ target +'">$1</a> ') );
    });
}

