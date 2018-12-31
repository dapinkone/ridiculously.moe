// should "use strict";
function decodeHtmlEntities(words) {
    let n = document.createElement('div');
    n.innerHTML = words;
    words = n.firstChild.nodeValue;

    // ;_;
    words = words.replace(/&(\d+);/gm,
                          function (_, match, _, _) {
                              return String.fromCharCode(match);
                          });
    return words;
}
function tagcloud(tags, parent=document.body) {
    for(let i = 0; i < tags.length; i++){
        let link = document.createElement("A");
        link.text = decodeHtmlEntities(tags[i]);
        link.href = '/search?q=' + encodeURI(link.text);

        link.className = "tag";
        parent.append(link);
    }
}
