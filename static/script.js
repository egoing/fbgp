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

var app = angular.module("app", []);
app.config(function ($interpolateProvider) { $interpolateProvider.startSymbol('[['); $interpolateProvider.endSymbol(']]'); })
app.controller("homeCtrl", function($scope, $http) {
    $scope.feed = {}
    $scope.active = {
        member:{
            key:'',
            entries:[],
            type:'post'
        }
    };
    $scope.feed.loading = false;
    $scope.post = function(next_cursor){
        $scope.feed.loading = true;
        $http.get("/feeddata/"+(jQuery('#content').data('tag'))+"?cursor="+(next_cursor ? next_cursor : '')).success(function(response) {
            if($scope.feed.posts){
                $scope.feed.posts =  $scope.feed.posts.concat(response.feeds);
            } else {
                $scope.feed.posts = response.feeds;
            }
            $scope.feed.more = response.more;
            $scope.feed.next_cursor = response.cursor;
            $scope.feed.loading = false;
        });
    }
    $scope.comment = function(post_key){
        var target;
        for(var name in $scope.feed.posts){
            if($scope.feed.posts[name]['key_urlsafe'] == post_key) {
                target = $scope.feed.posts[name];
            }
        }
        if(target){
            $http.get('/commentdata/'+post_key+(target.comment_next_cursor ? '?next_cursor=' + target.comment_next_cursor : '')).success(function(response) {
                if(!target.comments)
                    target.comments = [];
                target.comment_more = response.more;
                target.comment_next_cursor = response.next_cursor;
                target.comments = target.comments.concat(response.entries);
            })    
        }
    }
    $scope.member = function($event, type, member_key){
        $http({
            url:'/member_ajax/'+type,
            method:'GET',
            params: {member:member_key}
        }).success(function(response) {
            if($scope.active.member.key != member_key || $scope.active.member.type != type) {
                $scope.active.member.entries = response.entries;
            } else {
                $scope.active.member.entries = $scope.active.member.entries.concat(response.entries);
            }
            $scope.active.member.key = member_key;
            $scope.active.member.type = type;
            jQuery('#modal').modal();
        })
        $event.preventDefault();
    }
    $scope.post($scope.tag);
})