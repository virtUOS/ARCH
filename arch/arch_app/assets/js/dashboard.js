import Plotly from "plotly.js-dist";

export function dashboard() {

    var graph_records = document.getElementById('graph-records');
    // reformat string to array
    var x = graph_records.getAttribute("data-x").replace("[", "").replace("]", "").replaceAll("'", "").replaceAll(" ", "").split(",")
    var y = graph_records.getAttribute("data-y").replace("[", "").replace("]", "").split(",");

    var trace = {
        x: x,  //  ['2020-10-04', '2021-08-04', '2021-11-04'],
        y: y,  // [90, 40, 60],
        type: 'bar'
    };
    var data = [trace];
    var layout = {
        title: 'Record Uploads',
        showlegend: false
    };
    Plotly.newPlot(graph_records, data, layout, {staticPlot: true});

    var graph_logins = document.getElementById('graph-logins');
    var x = graph_logins.getAttribute("data-x").replace("[", "").replace("]", "").replaceAll("'", "").replaceAll(" ", "").split(",")
    var y = graph_logins.getAttribute("data-y").replace("[", "").replace("]", "").split(",");
    var trace = {
        x: x,
        y: y,
        type: 'bar'
    };
    var data = [trace];
    var layout = {
        title: 'Visits',
        showlegend: false
    };
    Plotly.newPlot(graph_logins, data, layout, {staticPlot: true});

    var graph_record_views = document.getElementById('graph-record_views');
    var x = graph_record_views.getAttribute("data-x").replace("[", "").replace("]", "").replaceAll("'", "").replaceAll(" ", "").split(",")
    var y = graph_record_views.getAttribute("data-y").replace("[", "").replace("]", "").split(",");
    var trace = {
        x: x,
        y: y,
        type: 'bar'
    };
    var data = [trace];
    var layout = {
        title: 'Record Views',
        showlegend: false
    };
    Plotly.newPlot(graph_record_views, data, layout, {staticPlot: true});

    var graph_albums = document.getElementById('graph-albums');
    var x = graph_albums.getAttribute("data-x").replace("[", "").replace("]", "").replaceAll("'", "").replaceAll(" ", "").split(",")
    var y = graph_albums.getAttribute("data-y").replace("[", "").replace("]", "").split(",");
    var trace = {
        x: x,
        y: y,
        type: 'bar'
    };
    var data = [trace];
    var layout = {
        title: 'Albums Views',
        showlegend: false
    };
    Plotly.newPlot(graph_albums, data, layout, {staticPlot: true});

    // create pie plot with member VS moderator uploads
    var graph_upload_ratio = document.getElementById('upload-ratio');
    var uploads_mods = graph_upload_ratio.getAttribute("data-uploads-mod");
    var uploads_members = graph_upload_ratio.getAttribute("data-uploads-member");

    var data = [{
        values: [uploads_mods, uploads_members],
        labels: ['Moderators', 'Members'],
        type: 'pie',
        textinfo: "value+percent",
    }];
    var layout = {
        title: 'Uploads by Moderators and Members',
    };
    Plotly.newPlot(graph_upload_ratio, data, layout, {staticPlot: true});

};

function create_graph(graph_id, x, y, title) {
    var graph = document.getElementById(graph_id);
    var trace = {
        x: x,
        y: y,
        type: 'bar'
    };
    var data = [trace];
    var layout = {
        title: title,
        showlegend: false
    };
    Plotly.newPlot(graph, data, layout, {staticPlot: true});
}
