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
                    var row_str = '';
                    var row = [];
                    for(var i = 0 ; i < result.feeds.length ; i++){
                        var feed = result.feeds[i];
                        row_str +=  '<tr><td class="entry" data-post_key="'+feed['key_urlsafe']+'">'
                        row_str += feed['full_picture'] ? '<div class="picture"><img src="'+feed['full_picture']+'" /></div>' : '';
                        row_str += '<div class="message">'+message(feed['message'])+'</div>';
                        row_str += '<div class="meta">'
                        row_str += '<span class="comment"><a href="#comment" class="comment_btn">댓글</a></span> |  ';
                        row_str += '<span class="member"><a href="/member/post?member='+feed['member']['key_urlsafe']+'">'+feed['member']['name']+'</a></span> | ';
                        row_str += '<span class="created_time"><a href="/post/'+feed['source_id']+'">'+feed['created_time']+'</a></span>';
                        row_str += '</div>';
                        row_str += '<div class="comment"><ul class="comment_data"></ul><button class="comment_more_btn">더보기</button></div>';
                        row_str += '</td></tr>';
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
        $('body').on('click', '.comment_btn, .comment_more_btn', function(){
            $this = $(this)
            $entry = $this.parents('.entry');
            $comment = $entry.find('.comment')
            $more = $entry.find('.comment_more_btn')
            $data = $entry.find('.comment_data')
            $.ajax({
                url:/commentdata/+$entry.data('post_key'),
                dataType:'json',
                type:'get',
                data:{next_cursor:$comment.data('next_cursor')},
                success:function(result){
                    str = ''
                    for(var i=0; i<result.entries.length; i++){
                        str += '<li>' + result.entries[i].message
                        str += ' <span class="name"><a href="/member/comment?member='+result.entries[i].member.key_urlsafe+'">'+result.entries[i].member.name+'</a></span>, '
                        str += ' <span class="date">'+result.entries[i].created_time+'</span></li>'    
                    }
                    if(result.next_cursor && result.more) {$more.show() } else {$more.hide() }
                    $comment.data('next_cursor', result.next_cursor)
                    $data.append(str)
                }
            })
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