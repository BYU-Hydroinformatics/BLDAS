/*****************************************************************************
 * FILE:    MAP JS
 * DATE:    5 APRIL 2018
 * AUTHOR: Sarva Pulla, Rohit Khattar
 * COPYRIGHT: (c) ICIMOD 2018
 * LICENSE: BSD 2-Clause
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

const geoserverURL = `http://tethys.servirglobal.net:8181/geoserver/wms`;

var LIBRARY_OBJECT = (function() {
    // Wrap the library in a package function
    "use strict"; // And enable strict mode for this library

    /************************************************************************
     *                      MODULE LEVEL / GLOBAL VARIABLES
     *************************************************************************/
    var animationDelay,
        current_layer,
        current_feature,
        feature_layer,
        dekad_options,
        districtLayer,
        element,
        $interactionModal,
        layers,
        $loading,
        map,
        month_options,
        popup,
        $plotter,
        $plotModal,
        public_interface, // Object returned by the module
        quarter_options,
        selectedFeatures,
        select_layer,
        select_source,
        sliderInterval,
        slider_max,
        styling,
        variable_data,
        variable_wms,
        $tsplotModal,
        wms_url,
        wms_layer,
        wms_source;

    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/
    var animate,
        add_wms,
        clear_coords,
        get_plot,
        get_styling,
        gen_color_bar,
        gen_slider,
        init_events,
        init_jquery_vars,
        init_dropdown,
        init_all,
        init_map,
        update_wms,
        get_lis_data;

    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS
     *************************************************************************/

    clear_coords = function() {
        $("#poly-lat-lon").val("");
        $("#point-lat-lon").val("");
    };

    init_jquery_vars = function() {
        var $meta_element = $("#metadata");
        dekad_options = $meta_element.attr("data-dekad-options");
        dekad_options = JSON.parse(dekad_options);
        month_options = $meta_element.attr("data-month-options");
        month_options = JSON.parse(month_options);
        quarter_options = $meta_element.attr("data-quarter-options");
        quarter_options = JSON.parse(quarter_options);
        variable_data = $meta_element.attr("data-variable-info");
        variable_data = JSON.parse(variable_data);
        wms_url = $meta_element.attr("data-wms-url");
        $plotModal = $("#plot-modal");
        $tsplotModal = $("#ts-plot-modal");
        $loading = $("#view-file-loading");
        $plotter = $("#plotter");
        animationDelay = 2000;
        sliderInterval = {};
    };

    init_dropdown = function() {
        $(".var_table").select2();
        $(".year_table").select2();
        $(".interval_table").select2();
        $(".date_table").select2();
        $(".variable_table_plot").select2();

        variable_data.forEach(function(item, i) {
            var new_option = new Option(
                item["display_name"] + " (" + item["units"] + ")",
                item["id"]
            );
            $("#variable_table_plot").append(new_option);
            var viz_option = new Option(
                item["display_name"] + " (" + item["units"] + ")",
                item["gs_id"]
            );
            $("#var_table").append(viz_option);
        });
    };

    init_map = function() {
        var projection = ol.proj.get("EPSG:3857");
        var baseLayer = new ol.layer.Tile({
            source: new ol.source.BingMaps({
                key:
                    "5TC0yID7CYaqv3nVQLKe~xWVt4aXWMJq2Ed72cO4xsA~ApdeyQwHyH_btMjQS1NJ7OHKY8BK-W-EMQMrIavoQUMYXeZIQOUURnKGBOC7UCt4",
                imagerySet: "AerialWithLabels" // Options 'Aerial', 'AerialWithLabels', 'Road'
            })
        });
        var fullScreenControl = new ol.control.FullScreen();
        var view = new ol.View({
            center: ol.proj.transform([90.3, 23.6], "EPSG:4326", "EPSG:3857"),
            projection: projection,
            zoom: 5
        });
        wms_source = new ol.source.ImageWMS({
            url: wms_url,
            params: {},
            serverType: "geoserver",
            crossOrigin: "Anonymous"
        });

        wms_layer = new ol.layer.Image({
            name: "wms_layer",
            source: wms_source
        });

        var vector_source = new ol.source.Vector({
            wrapX: false
        });

        var vector_layer = new ol.layer.Vector({
            name: "my_vectorlayer",
            source: vector_source,
            style: new ol.style.Style({
                fill: new ol.style.Fill({
                    color: "rgba(255, 255, 255, 0.2)"
                }),
                stroke: new ol.style.Stroke({
                    color: "#ffcc33",
                    width: 2
                }),
                image: new ol.style.Circle({
                    radius: 7,
                    fill: new ol.style.Fill({
                        color: "#ffcc33"
                    })
                })
            })
        });

        var default_style = new ol.style.Style({
            fill: new ol.style.Fill({
                color: [250, 250, 250, 0.1]
            }),
            stroke: new ol.style.Stroke({
                color: [220, 220, 220, 1],
                width: 4
            })
        });

        select_source = new ol.source.Vector();

        select_layer = new ol.layer.Vector({
            name: "select_layer",
            source: select_source,
            style: default_style
        });

        districtLayer = new ol.layer.Tile({
            name: "districts",
            source: new ol.source.TileWMS({
                crossOrigin: "anonymous", // // KS Refactor Design 2016 Override // This should enable screenshot export around the CORS issue with Canvas.
                url: geoserverURL,
                params: {
                    LAYERS: "utils:adminOne",
                    TILED: true
                },
                serverType: "geoserver"
            })
        });

        feature_layer = new ol.layer.Image({
            source: new ol.source.ImageWMS({
                url: "http://tethys.icimod.org:8181/geoserver/hydroviewer/wms",
                params: {
                    LAYERS: "hydroviewer:nepal-national-drainage_line-3857"
                },
                serverType: "geoserver",
                crossOrigin: "Anonymous"
            })
        });

        layers = [
            baseLayer,
            wms_layer,
            districtLayer,
            vector_layer,
            select_layer,
            feature_layer
        ];

        map = new ol.Map({
            target: document.getElementById("map"),
            layers: layers,
            view: view
        });

        districtLayer.setVisible(false);
        map.crossOrigin = "anonymous";
        element = document.getElementById("popup");

        popup = new ol.Overlay({
            element: element,
            positioning: "bottom-center",
            stopEvent: true
        });

        map.addOverlay(popup);

        //Code for adding interaction for drawing on the map
        var lastFeature, draw, featureType;

        //Clear the last feature before adding a new feature to the map
        var removeLastFeature = function() {
            if (lastFeature) vector_source.removeFeature(lastFeature);
        };

        //Add interaction to the map based on the selected interaction type
        var addInteraction = function(geomtype) {
            var typeSelect = document.getElementById("interaction-type");
            var value = typeSelect.value;
            $("#data").val("");
            if (value !== "None") {
                if (draw) map.removeInteraction(draw);

                draw = new ol.interaction.Draw({
                    source: vector_source,
                    type: geomtype
                });

                map.addInteraction(draw);
            }
            if (featureType === "Point" || featureType === "Polygon") {
                draw.on("drawend", function(e) {
                    lastFeature = e.feature;
                });

                draw.on("drawstart", function(e) {
                    vector_source.clear();
                });
            }
        };

        vector_layer.getSource().on("addfeature", function(event) {
            //Extracting the point/polygon values from the drawn feature
            var feature_json = saveData();
            var parsed_feature = JSON.parse(feature_json);
            var feature_type =
                parsed_feature["features"][0]["geometry"]["type"];
            if (feature_type == "Point") {
                $plotModal.find(".info").html("");
                var coords =
                    parsed_feature["features"][0]["geometry"]["coordinates"];
                var proj_coords = ol.proj.transform(
                    coords,
                    "EPSG:3857",
                    "EPSG:4326"
                );
                $("#point-lat-lon").val(proj_coords);
                $plotModal
                    .find(".info")
                    .html(
                        "<b>You have selected a point at " +
                            proj_coords[1].toFixed(2) +
                            "," +
                            proj_coords[0].toFixed(2) +
                            ". Click on Show plot to view the Time series.</b>"
                    );
                $plotModal.modal("show");
            } else if (feature_type == "Polygon") {
                $plotModal.find(".info").html("");
                var coords =
                    parsed_feature["features"][0]["geometry"]["coordinates"][0];
                proj_coords = [];
                coords.forEach(function(coord) {
                    var transformed = ol.proj.transform(
                        coord,
                        "EPSG:3857",
                        "EPSG:4326"
                    );
                    proj_coords.push("[" + transformed + "]");
                });
                var json_object =
                    '{"type":"Polygon","coordinates":[[' + proj_coords + "]]}";
                $("#poly-lat-lon").val(json_object);
                $plotModal
                    .find(".info")
                    .html(
                        "<b>You have selected the following polygon object " +
                            proj_coords +
                            ". Click on Show plot to view the Time series.</b>"
                    );
                $plotModal.modal("show");
            }
        });

        function saveData() {
            // get the format the user has chosen
            var data_type = "GeoJSON",
                // define a format the data shall be converted to
                format = new ol.format[data_type](),
                // this will be the data in the chosen format
                data;
            try {
                // convert the data of the vector_layer into the chosen format
                data = format.writeFeatures(
                    vector_layer.getSource().getFeatures()
                );
            } catch (e) {
                // at time of creation there is an error in the GPX format (18.7.2014)
                $("#data").val(e.name + ": " + e.message);
                return;
            }
            // $('#data').val(JSON.stringify(data, null, 4));
            return data;
        }
        $("#interaction-type")
            .change(function(e) {
                featureType = $(this)
                    .find("option:selected")
                    .val();
                clear_coords();
                select_source.clear();
                selectedFeatures = [];
                vector_layer.getSource().clear();
                districtLayer.setVisible(false);
                wms_layer.setVisible(true);
                map.removeInteraction(draw);
                if (featureType == "None") {
                    wms_layer.setVisible(true);
                } else {
                    wms_layer.setVisible(false);
                }
                if (featureType == "None") {
                    $("#data").val("");

                    map.removeInteraction(draw);
                    vector_layer.getSource().clear();
                } else if (featureType == "Point") {
                    addInteraction(featureType);
                } else if (featureType == "Polygon") {
                    addInteraction(featureType);
                } else if (featureType == "District") {
                    districtLayer.setVisible(true);
                    wms_layer.setVisible(false);
                }
            })
            .change();
    };

    init_events = function() {
        (function() {
            var target, observer, config;
            // select the target node
            target = $("#app-content-wrapper")[0];

            observer = new MutationObserver(function() {
                window.setTimeout(function() {
                    map.updateSize();
                }, 350);
            });
            $(window).on("resize", function() {
                map.updateSize();
            });

            config = {
                attributes: true
            };

            observer.observe(target, config);
        })();

        map.on("singleclick", function(evt) {
            $(element).popover("destroy");

            if (
                $("#interaction-type")
                    .find("option:selected")
                    .val() == "None" ||
                $("#interaction-type")
                    .find("option:selected")
                    .val() == "District"
            ) {
                var clickCoord = evt.coordinate;
                var view = map.getView();
                var viewResolution = view.getResolution();

                var wms_url = current_layer
                    .getSource()
                    .getGetFeatureInfoUrl(
                        evt.coordinate,
                        viewResolution,
                        view.getProjection(),
                        {
                            INFO_FORMAT: "application/json"
                        }
                    ); //Get the wms url for the clicked point

                if (current_layer.get("name") == "wms_layer") {
                    popup.setPosition(clickCoord);
                    if (wms_url) {
                        //Retrieving the details for clicked point via the url
                        $.ajax({
                            type: "GET",
                            url: wms_url,
                            dataType: "json",
                            success: function(result) {
                                var value = parseFloat(
                                    result["features"][0]["properties"][
                                        "GRAY_INDEX"
                                    ]
                                );
                                value = value.toFixed(2);
                                $(element).popover({
                                    placement: "top",
                                    html: true,
                                    //Dynamically Generating the popup content
                                    content: "Value: " + value
                                });

                                $(element).popover("show");
                                $(element)
                                    .next()
                                    .css("cursor", "text");
                            },
                            error: function(
                                XMLHttpRequest,
                                textStatus,
                                errorThrown
                            ) {
                                console.log(error);
                            }
                        });
                    }
                } else if (current_layer.get("name") == "districts") {
                    $.ajax({
                        type: "GET",
                        url: wms_url,
                        dataType: "json",
                        success: function(result) {
                            $plotModal.find(".info").html("");
                            select_source.clear();
                            selectedFeatures = [];
                            var selFeature = result["features"][0];

                            var format = new ol.format.GeoJSON({
                                defaultDataProjection: "EPSG:4326",
                                featureProjection: "EPSG:3857"
                            });
                            var feature = format.readFeature(selFeature, {
                                dataProjection: "EPSG:4326",
                                featureProjection: "EPSG:3857"
                            });

                            if (
                                selectedFeatures.indexOf(
                                    JSON.stringify(selFeature)
                                ) == -1
                            ) {
                                selectedFeatures.push(
                                    JSON.stringify(selFeature)
                                );
                                select_source.addFeature(feature);
                            }

                            $plotModal.modal("show");
                        },
                        error: function(
                            XMLHttpRequest,
                            textStatus,
                            errorThrown
                        ) {
                            console.log(error);
                        }
                    });
                } else {
                    if (wms_url) {
                        $("#chartloc").html('');
                        $.ajax({
                            type: "GET",
                            url: wms_url,
                            dataType: "json",
                            success: function(result) {
                                let comid =
                                    result["features"][0]["properties"][
                                        "COMID"
                                    ];

                                get_lis_data(comid);
                            },
                            error: function(err) {
                                console.log(error);
                            }
                        });
                    }
                }
            }
        });

        map.on("pointermove", function(evt) {
            if (evt.dragging) {
                return;
            }

            var pixel = map.getEventPixel(evt.originalEvent);

            let hit = map.forEachLayerAtPixel(pixel, layer => {
                if (
                    layer != layers[0] &&
                    layer != layers[3] &&
                    layer != layers[4]
                ) {
                    current_layer = layer;
                    return true;
                }
            });
            map.getTargetElement().style.cursor = hit ? "pointer" : "";
        });
    };

    init_all = function() {
        init_jquery_vars();
        init_dropdown();
        init_map();
        init_events();
    };

    gen_color_bar = function(colors, scale) {
        // var cv  = document.getElementById('cv'),
        //     ctx = cv.getContext('2d');
        // ctx.clearRect(0,0,cv.width,cv.height);
        // var variable = $("#var_table option:selected").val();
        // var fixed;
        // if(variable=='rain' || variable=='evap'){
        //     fixed = 5;
        // }else{
        //     fixed = 0;
        // }
        // colors.forEach(function(color,i){
        //     ctx.beginPath();
        //     ctx.fillStyle = color;
        //     ctx.fillRect(0,i*20,20,30);
        //     ctx.fillText(scale[i].toFixed(fixed),30,i*20);
        // });
    };

    get_styling = function(start, end, scale) {
        var sld_color_string = "";
        if (scale[scale.length - 1] == 0) {
            var colors = chroma
                .scale([start, start])
                .mode("lab")
                .correctLightness()
                .colors(20);
            // var colors2 = chroma.scale([start,start]).classes(20);
            // console.log(colors2);
            gen_color_bar(colors, scale);
            var color_map_entry =
                '<ColorMapEntry color="' +
                colors[0] +
                '" quantity="' +
                scale[0] +
                '" label="label1" opacity="0.7"/>';
            sld_color_string += color_map_entry;
        } else {
            var colors = chroma
                .scale([start, end])
                .mode("lab")
                .correctLightness()
                .colors(20);
            // var colors2 = chroma.scale([start,end]).classes(20);
            // console.log(colors);
            gen_color_bar(colors, scale);
            colors.forEach(function(color, i) {
                var color_map_entry =
                    '<ColorMapEntry color="' +
                    color +
                    '" quantity="' +
                    scale[i] +
                    '" label="label' +
                    i +
                    '" opacity="0.7"/>';
                sld_color_string += color_map_entry;
            });
        }

        return sld_color_string;
    };

    add_wms = function(workspace, variable, year, date_type, interval_type) {
        map.removeLayer(wms_layer);
        var layer_name = workspace + ":" + variable + "_" + year + date_type;
        //console.log(layer_name);
        var index = find_gsvar_index(variable, variable_data);

        variable_wms = variable;
        document.getElementById("imageBox").src =
            "http://tethys.icimod.org:8181/geoserver/saldas" +
            interval_type +
            "/wms?REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&style=" +
            variable +
            "&WIDTH=10&HEIGHT=10&LAYER=" +
            layer_name +
            "&legend_options=fontName:Times%20New%20Roman;fontAntiAliasing:true;fontColor:0x000033;fontSize:6;bgColor:0xFFFFEE;dpi:180";

        //'SLD_BODY':sld_string
        wms_source = new ol.source.ImageWMS({
            url: wms_url,
            // params: {'LAYERS':layer_name,'SLD_BODY':sld_string},
            params: {
                LAYERS: layer_name,
                STYLES: variable_wms
            },
            serverType: "geoserver",
            crossOrigin: "Anonymous"
        });

        wms_layer = new ol.layer.Image({
            name: "wms_layer",
            source: wms_source
        });

        // wms_source.updateParams({'LAYERS':layer_name,'SLD_BODY':sld_string});
        map.getLayers().insertAt(2, wms_layer);

        //var layer_extent = [11.3,-26.75,58.9,14.0];
        //var transformed_extent = ol.proj.transformExtent(layer_extent,'EPSG:4326','EPSG:3857');
        //map.getView().fit(transformed_extent,map.getSize());
        map.updateSize();
    };

    update_wms = function(workspace, variable, year, date_type, interval_type) {
        var layer_name = workspace + ":" + variable + "_" + year + date_type;
        // wms_source.updateParams({'LAYERS':layer_name,'SLD_BODY':sld_string});

        wms_source.updateParams({
            LAYERS: layer_name,
            STYLES: variable_wms
        });
    };

    gen_slider = function(interval) {
        if (interval == "DD") {
            slider_max = dekad_options.length;
            $("#slider").slider({
                value: 1,
                min: 0,
                max: dekad_options.length - 1,
                step: 1, //Assigning the slider step based on the depths that were retrieved in the controller
                animate: "fast",
                slide: function(event, ui) {}
            });
        } else if (interval == "MM") {
            slider_max = month_options.length + 1;
            $("#slider").slider({
                value: 1,
                min: 0,
                max: month_options.length - 1,
                step: 1, //Assigning the slider step based on the depths that were retrieved in the controller
                animate: "fast",
                slide: function(event, ui) {}
            });
        } else if (interval == "3M") {
            slider_max = quarter_options.length + 1;
            $("#slider").slider({
                value: 1,
                min: 0,
                max: quarter_options.length - 1,
                step: 1, //Assigning the slider step based on the depths that were retrieved in the controller
                animate: "fast",
                slide: function(event, ui) {}
            });
        }
    };

    get_lis_data = function(comid) {
        $(".info").html("");
        $tsplotModal.modal("show");
        $loading.removeClass("hidden");
        $plotter.addClass("hidden");

        $.ajax({
            type: "GET",
            url: "get-lis-time-series/",
            data: {
                comid
            },
            error: function(err) {
                  $(".info").html(
                        "<b>Error processing the request." + err
                    );
                $loading.addClass("hidden");
                $("#chartloc").html('');
            },
            success: data => {
                $("#chartloc").html(data);
                
                $loading.addClass("hidden");
            }
        });
    };

    get_plot = function() {
        $(".info").html("");
        $plotModal.modal("hide");
        $tsplotModal.modal("show");
        $loading.removeClass("hidden");
        $plotter.addClass("hidden");
        var variable = $("#variable_table_plot option:selected").val();
        var point = $("#point-lat-lon").val();
        var polygon = $("#poly-lat-lon").val();
        var interaction = $("#interaction-type option:selected").val();
        var interval_type = $("#interval_table option:selected").val();
        var year = $("#year_table option:selected").val();
        var geom_data;
        if (interaction == "Point") {
            geom_data = $("#point-lat-lon").val();
        } else if (interaction == "Polygon") {
            geom_data = $("#poly-lat-lon").val();
        } else if (interaction == "District") {
            geom_data = selectedFeatures;
        }

        var xhr = ajax_update_database("get-plot", {
            year: year,
            interval: interval_type,
            variable: variable,
            geom_data: geom_data,
            interaction: interaction
        });
        xhr
            .done(function(data) {
                if ("success" in data) {
                    //                    if(data.interaction == "point"){
                    //                    var index = find_var_index(variable,variable_data);
                    //                    var display_name = variable_data[index]["display_name"];
                    //                    var units = variable_data[index]["units"];
                    //                    $("#plotter").highcharts({
                    //                        chart: {
                    //                            type:'area',
                    //                            zoomType: 'x'
                    //                        },
                    //                        title: {
                    //                            text: 'Values for ' + display_name
                    //                            // style: {
                    //                            //     fontSize: '13px',
                    //                            //     fontWeight: 'bold'
                    //                            // }
                    //                        },
                    //                        xAxis: {
                    //                            type: 'datetime',
                    //                            labels: {
                    //                                format: '{value:%d %b %Y}'
                    //                                // rotation: 90,
                    //                                // align: 'left'
                    //                            },
                    //                            title: {
                    //                                text: 'Date'
                    //                            }
                    //                        },
                    //                        yAxis: {
                    //                            title: {
                    //                                text: units
                    //                            }
                    //
                    //                        },
                    //                        exporting: {
                    //                            enabled: true
                    //                        },
                    //                        series: [{
                    //                            data:data.time_series,
                    //                            name: display_name
                    //                        }]
                    //                    });
                    //                    $plotter.removeClass('hidden');
                    //                    $loading.addClass('hidden');
                    //}
                    if (
                        data.interaction == "district" ||
                        data.interaction == "polygon" ||
                        data.interaction == "point"
                    ) {
                        var index = find_var_index(variable, variable_data);
                        var display_name = variable_data[index]["display_name"];
                        var units = variable_data[index]["units"];

                        Highcharts.chart("plotter", {
                            chart: {
                                type: "line",
                                zoomType: "x"
                            },
                            title: {
                                text: "Values for " + display_name
                            },
                            plotOptions: {
                                series: {
                                    marker: {
                                        enabled: true
                                    },
                                    allowPointSelect: true,
                                    cursor: "pointer"
                                }
                            },
                            xAxis: {
                                type: "datetime",
                                labels: {
                                    format: "{value:%d %b %Y}"
                                    // rotation: 90,
                                    // align: 'left'
                                },
                                title: {
                                    text: "Date"
                                }
                            },
                            yAxis: {
                                title: {
                                    text: units
                                }
                            },
                            exporting: {
                                enabled: true
                            },
                            series: [
                                {
                                    data: data.time_series["min_data"],
                                    name: "Min Values"
                                },
                                {
                                    data: data.time_series["max_data"],
                                    name: "Max Values"
                                },
                                {
                                    data: data.time_series["median_data"],
                                    name: "Median Values"
                                },
                                {
                                    data: data.time_series["mean_data"],
                                    name: "Mean Values"
                                }
                            ]
                        });
                        $plotter.removeClass("hidden");
                        $loading.addClass("hidden");
                    }
                } else {
                    $(".info").html(
                        "<b>Error processing the request. Please be sure to click on a feature." +
                            data.error +
                            "</b>"
                    );
                    $("#info").removeClass("hidden");
                    $plotter.removeClass("hidden");
                    $loading.addClass("hidden");
                }
            })
            .error(function(data) {
                $(".info").html(
                    "<b>Error processing the request. Please be sure to click on a feature." +
                        data.error +
                        "</b>"
                );
                $("#info").removeClass("hidden");
                $plotter.removeClass("hidden");
                $loading.addClass("hidden");
            });
    };

    $("#btn-get-plot").click(get_plot);

    animate = function() {
        var sliderVal = $("#slider").slider("value");

        sliderInterval = setInterval(function() {
            $("#slider").slider("value", sliderVal);
            sliderVal += 1;
            if (sliderVal === slider_max - 1) sliderVal = 0;
        }, animationDelay);
    };

    $(".btn-run").on("click", animate);
    //Set the slider value to the current value to start the animation at the );
    $(".btn-stop").on("click", function() {
        //Call clearInterval to stop the animation.
        clearInterval(sliderInterval);
    });

    $(".btn-increase").on("click", function() {
        clearInterval(sliderInterval);

        if (animationDelay > 250) {
            animationDelay = animationDelay - 250;
            $("#speed").val((1 / (animationDelay / 1000)).toFixed(2));
            animate();
        }
    });

    //Decrease the slider timer when you click decrease the speed
    $(".btn-decrease").on("click", function() {
        clearInterval(sliderInterval);
        animationDelay = animationDelay + 250;
        $("#speed").val((1 / (animationDelay / 1000)).toFixed(2));
        animate();
    });

    /************************************************************************
     *                        DEFINE PUBLIC INTERFACE
     *************************************************************************/

    public_interface = {};

    /************************************************************************
     *                  INITIALIZATION / CONSTRUCTOR
     *************************************************************************/

    // Initialization: jQuery function that gets called when
    // the DOM tree finishes loading
    $(function() {
        init_all();

        $("#var_table").change(function() {
            $("#date_table").change();
        });

        $("#year_table").change(function() {
            // var year = ($("#year_table option:selected").val());
            // alert("Start: " + year)
        });

        $("#interval_table")
            .change(function() {
                var d = new Date();
                var n = d.getMonth() + 1;
                var interval_type = $("#interval_table option:selected").val();
                gen_slider(interval_type);
                $("#date_table").html("");
                var year = $("#year_table option:selected").val();

                if (interval_type == "DD") {
                    if (year == "2018") {
                        dekad_options.forEach(function(date, i) {
                            var chkDate = parseInt(date[0]);
                            if (chkDate < n * 100) {
                                var new_option = new Option(date[1], date[0]);
                                if (i == 0) {
                                    $("#date_table")
                                        .append(new_option)
                                        .trigger("change");
                                } else {
                                    $("#date_table").append(new_option);
                                }
                            }
                            var date_type = $(
                                "#date_table option:selected"
                            ).val();
                        });
                    } else {
                        dekad_options.forEach(function(date, i) {
                            var new_option = new Option(date[1], date[0]);
                            if (i == 0) {
                                $("#date_table")
                                    .append(new_option)
                                    .trigger("change");
                            } else {
                                $("#date_table").append(new_option);
                            }
                            var date_type = $(
                                "#date_table option:selected"
                            ).val();
                        });
                    }
                } else if (interval_type == "MM") {
                    month_options.forEach(function(date, i) {
                        if (year == "2018") {
                            var new_option = new Option(date[1], date[0]);
                            var chkDate = parseInt(date[0]);
                            if (chkDate < n) {
                                if (i == 0) {
                                    $("#date_table")
                                        .append(new_option)
                                        .trigger("change");
                                } else {
                                    $("#date_table").append(new_option);
                                }
                            }
                        } else {
                            var new_option = new Option(date[1], date[0]);
                            if (i == 0) {
                                $("#date_table")
                                    .append(new_option)
                                    .trigger("change");
                            } else {
                                $("#date_table").append(new_option);
                            }
                        }
                    });
                } else if (interval_type == "3M") {
                    quarter_options.forEach(function(date, i) {
                        if (year == "2018") {
                            var chkDate = parseInt(date[0]);
                            var new_option = new Option(date[1], date[0]);
                            if (chkDate < n * 10000) {
                                if (i == 0) {
                                    $("#date_table")
                                        .append(new_option)
                                        .trigger("change");
                                } else {
                                    $("#date_table").append(new_option);
                                }
                            }
                        } else {
                            var new_option = new Option(date[1], date[0]);
                            if (i == 0) {
                                $("#date_table")
                                    .append(new_option)
                                    .trigger("change");
                            } else {
                                $("#date_table").append(new_option);
                            }
                        }
                    });
                }
            })
            .change();

        $("#date_table")
            .change(function() {
                $("#interaction-type")
                    .val("None")
                    .trigger("change");
                var interval_type = $("#interval_table option:selected").val();
                var date_type = $("#date_table option:selected").val();
                var year = $("#year_table option:selected").val();
                var variable = $("#var_table option:selected").val();
                var workspace = "saldas" + interval_type;
                add_wms(workspace, variable, year, date_type, interval_type);
                var selected_option = $(this)
                    .find("option:selected")
                    .index();
                $("#slider").slider("value", selected_option);
                //$('#slider').trigger('change');
            })
            .change();

        $("#slider").on("slidechange", function(event, ui) {
            var date_text = $("#date_table option")[ui.value].text;
            $("#slider-text").text(date_text); //Get the value from the slider
            var date_value = $("#date_table option")[ui.value].value;
            var interval_type = $("#interval_table option:selected").val();
            var year = $("#year_table option:selected").val();
            var variable = $("#var_table option:selected").val();
            var workspace = "saldas" + interval_type;
            update_wms(workspace, variable, year, date_value, interval_type);
            // alert(variable);
        });
    });

    return public_interface;
})(); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.
