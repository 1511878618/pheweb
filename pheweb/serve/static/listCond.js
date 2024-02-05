LocusZoom.Adapters.extend("AssociationLZ", "AssociationPheWeb_cond", {
    getURL: function (state, chain, fields) {
        return this.url + `chr=${state.chr}&start=${state.start}&end=${state.end}`;
    },
    // Although the layout fields array is useful for specifying transforms, this source will magically re-add
    //  any data that was not explicitly requested
    extractFields: function(data, fields, outnames, trans) {
        // The field "all" has a special meaning, and only exists to trigger a request to this source.
        // We're not actually trying to request a field by that name.
        var has_all = fields.indexOf("all");
        if (has_all !== -1) {
            fields.splice(has_all, 1);
            outnames.splice(has_all, 1);
            trans.splice(has_all, 1);
        }
        // Find all fields that have not been requested (sans transforms), and add them back to the fields array
        if (data.length) {
            var fieldnames = Object.keys(data[0]);
            var ns = this.source_id + ":"; // ensure that namespacing is applied to the fields
            fieldnames.forEach(function(item) {
                var ref = fields.indexOf(item);
                if (ref === -1 || trans[ref]) {
                    fields.push(item);
                    outnames.push(ns + item);
                    trans.push(null);
                }
            });
        }
        return LocusZoom.Adapters.get('AssociationLZ').prototype.extractFields.call(this, data, fields, outnames, trans);
    },

    normalizeResponse(data) {
        // The PheWeb region API has a fun quirk where if there is no data, there are also no keys
        //   (eg data = {} instead of  {assoc:[]} etc. Explicitly detect and handle the edge case in PheWeb;
        //   we won't handle this in LZ core because we don't want squishy-blob API schemas to catch on.
        if (!Object.keys(data).length) {
            return [];
        }
        return LocusZoom.Adapters.get('AssociationLZ').prototype.normalizeResponse.call(this, data);
    }
});


function createTableRow(item) {
    const row = document.createElement("tr");
    const checkboxCell = document.createElement("td");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.className = "form-check-input";
    checkboxCell.appendChild(checkbox);
  
    const chrCell = document.createElement("td");
    chrCell.textContent = item.chr;
  
    const startCell = document.createElement("td");
    startCell.textContent = item.start;
  
    const endCell = document.createElement("td");
    endCell.textContent = item.end;
  
    const phenocodeCell = document.createElement("td");
    phenocodeCell.textContent = item.phenocode;
  
    const condTimeCell = document.createElement("td");
    condTimeCell.textContent = item.condTime;
  
    const filePathCell = document.createElement("td");
    const downloadLink = document.createElement("a");
    downloadLink.href = window.location.origin+'/'+item.filePath;
    downloadLink.target = "_blank";
    downloadLink.textContent = "Download";
    filePathCell.appendChild(downloadLink);
  
    row.appendChild(checkboxCell);
    row.appendChild(chrCell);
    row.appendChild(startCell);
    row.appendChild(endCell);
    row.appendChild(phenocodeCell);
    row.appendChild(condTimeCell);
    row.appendChild(filePathCell);
  
    return row;
  }
  
  // Function to update the table with data from /api/cond
function updateTable() {
const chr = window.plot.state.chr;
const start = window.plot.state.start;
const end = window.plot.state.end;
const pheno = window.pheno["phenocode"]

// Make an AJAX request to /api/cond with the dynamic values
$.get(`/api/cond?phenocode=${pheno}&chr=${chr}&start=${start}&end=${end}`, function (data) {
    const newData = data.data; // Assuming data is the response JSON object
    const tableBody = $("#tableBody"); // Get the table body element using jQuery

    // Iterate through each new data item and create table rows
    // newData.forEach(item => {
    // const newRow = createTableRow(item);
    // tableBody.prepend(newRow); // Insert new row at the beginning of the table body
    // });
    if (newData.length === 0) {
        return; // Exit the function if newData is empty
    }

    newData.forEach(item => {
        // Check if the item already exists in the table by comparing content
        const existingRow = Array.from(tableBody.children()).find(row => {

            const item_list = $.trim($(row).context.innerText).split('\t')
            const rowContent = {"chr":item_list[0], "start":item_list[1], "end":item_list[2], "phenocode":item_list[3], "condTime":item_list[4]}
            const itemContent = {"chr":item["chr"], "start":item["start"], "end":item["end"], "phenocode":item["phenocode"], "condTime":item["condTime"]}

            return JSON.stringify(rowContent) === JSON.stringify(itemContent);
        });

        // If the item does not exist in the table, create a new row and prepend it
        if (!existingRow) {
            const newRow = createTableRow(item);
            tableBody.prepend(newRow); // Insert new row at the beginning of the table body; // Insert new row at the beginning of the table body
        }
    });

});
}

// Initial table update when the page loads

$(document).ready(function () {
    updateTable();

    // alert(window.plot)
    // Listen for changes in plot.state and update the table accordingly
    const listener = window.plot.on('state_changed',function () {
    updateTable();
    })
    
    const submitBtn = document.getElementById("submitBtn");
    window.model.already=[];

    submitBtn.addEventListener("click", function () {
        // 获取被选中的选项
        const checkedOptions = [];
        // const checkboxes = document.querySelectorAll('input[type="checkbox"]');

        const rows = document.querySelectorAll('#tableBody tr'); // Get all rows inside the tbody
        
        rows.forEach(function(row) {
            const checkbox = row.querySelector('input[type="checkbox"]'); // Get the checkbox element inside this row
            
            if (checkbox.checked) {
                // Assuming the index of the column you want is 5 (for example, the "condTime" column)
                const pathCell = row.cells[6];
                const condTime = row.cells[5]
                const downloadLink = pathCell.querySelector('a'); // Get the <a> element inside this row
                const downloadUrl = downloadLink.getAttribute('href'); // Get the "href" attribute value
                checkedOptions.push({"url":downloadUrl, "condTime":condTime.textContent});
                // console.log(downloadUrl);
            }
            
        });
            // 根据选项生成显示的文本
    if (checkedOptions.length === 0) {
        resultText = "你没有选择任何选项。";
      } else {
        for (var i = 1; i < checkedOptions.length+1; i++) {
            
            var file = checkedOptions[i-1].url;
            var condTime = checkedOptions[i-1].condTime
            // console.log(file)
            if (window.model.already.includes(file)) {
              } else {
                // console.log(condTime) 
                window.model.already.push(file)
                window.data_sources.add(`assoc_${condTime}`, ["AssociationPheWeb_cond", {url: "/query/cond/" + `?file=${file}&` }])
                window.model.tooltip_lztemplate
                window.model.tooltip
                window.plot.addPanel(function() {
                    // FIXME: The only customization here is to make the legend button green and hide the "move panel" buttons; displayn options doesn't need to be copy-pasted
                    var base = LocusZoom.Layouts.get("panel", "association_catalog", {
                        namespace: { assoc: `assoc_${condTime}` },
                        id: `assoc_${condTime}`,
                        title: { text: `cond_${condTime}`},
                        y_index:-i,
                        height: 200, min_height: 200,
                        margin: { top: 10 },
                        toolbar: {
                            widgets: [
                                {
                                    type: "toggle_legend",
                                    position: "right",
                                    color: "green"
                                },
                                {
                                    type: "display_options",
                                    position: "right",
                                    color: "blue",
                                    // Below: special config specific to this widget
                                    button_html: "Display options...",
                                    button_title: "Control how plot items are displayed",

                                    layer_name: "associationpvaluescatalog",
                                    default_config_display_name: "No catalog labels (default)", // display name for the default plot color option (allow user to revert to plot defaults)

                                    options: [
                                        {
                                            // First dropdown menu item
                                            display_name: "Label catalog traits",  // Human readable representation of field name
                                            display: {  // Specify layout directives that control display of the plot for this option
                                                label: {
                                                    text: "{{{{namespace[catalog]}}trait}}",
                                                    spacing: 6,
                                                    lines: {
                                                        style: {
                                                            "stroke-width": "2px",
                                                            "stroke": "#333333",
                                                            "stroke-dasharray": "2px 2px"
                                                        }
                                                    },
                                                    filters: [
                                                        // Only label points if they are significant for some trait in the catalog, AND in high LD
                                                        //  with the top hit of interest
                                                        {
                                                            field: "{{namespace[catalog]}}trait",
                                                            operator: "!=",
                                                            value: null
                                                        },
                                                        {
                                                            field: "{{namespace[catalog]}}log_pvalue",
                                                            operator: ">",
                                                            value: 7.301
                                                        },
                                                        {
                                                            field: "{{namespace[ld]}}state",
                                                            operator: ">",
                                                            value: 0.4
                                                        },
                                                    ],
                                                    style: {
                                                        "font-size": "10px",
                                                        "font-weight": "bold",
                                                        "fill": "#333333"
                                                    }
                                                }
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        data_layers: [
                            LocusZoom.Layouts.get("data_layer", "significance", { unnamespaced: true }),
                            LocusZoom.Layouts.get("data_layer", "recomb_rate", { unnamespaced: true }),
                            function() {
                                var l = LocusZoom.Layouts.get("data_layer", "association_pvalues_catalog", {
                                    unnamespaced: true,
                                    // namespace:{assoc:'`assoc_${condTime}`'},
                                    fields: [
                                        `{{namespace[assoc_${condTime}]}}all`, // special mock value for the custom source
                                        `{{namespace[assoc_${condTime}]}}id`,
                                        `{{namespace[assoc_${condTime}]}}position`,
                                        `{{namespace[assoc_${condTime}]}}pvalue|neglog10_or_323`,
                                        `{{namespace[ld]}}state`, `{{namespace[ld]}}isrefvar`,
                                    ],
                                    id_field: "{{namespace[assoc]}}id",
                                    tooltip: {
                                        closable: true,
                                        show: {
                                            "or": ["highlighted", "selected"]
                                        },
                                        hide: {
                                            "and": ["unhighlighted", "unselected"]
                                        },
                                        namespace:{assoc:`assoc_${condTime}`, ld:"ld"},
                                        html: 
                                        "<strong>{{{{namespace[assoc]}}id}}</strong><br><br>" +
                                        window.model.tooltip_lztemplate.replace(/{{/g, `{{assoc_${condTime}:`).replace(RegExp('{{assoc_' + condTime + ':#if ', 'g'), "{{#if {{namespace[assoc]}}").replace(RegExp('{{assoc_' + condTime + ':/if}}', 'g'), "{{/if}}")+"<a href=\"" + window.model.urlprefix+ "/variant/{{{{namespace[assoc]}}chr}}-{{{{namespace[assoc]}}position}}-{{{{namespace[assoc]}}ref}}-{{{{namespace[assoc]}}alt}}\"" + ">Go to PheWAS</a>" 
                                            // "<br>{{#if {{namespace[ld]}}isrefvar}}<strong>LD Reference Variant</strong>{{#else}}<a href=\"javascript:void(0);\" onclick=\"var data = this.parentNode.__data__;data.getDataLayer().makeLDReference(data);\">Make LD Reference</a>{{/if}}<br>"
                                    },
                                    x_axis: { field: "{{namespace[assoc]}}position" },
                                    y_axis: {
                                        axis: 1,
                                        field: "{{namespace[assoc]}}pvalue|neglog10_or_323",
                                        floor: 0,
                                        upper_buffer: 0.1,
                                        min_extent: [0, 10]
                                    }
                                });
                                l.behaviors.onctrlclick = [{
                                    action: "link",
                                    href: window.model.urlprefix+"/variant/{{{{namespace[assoc]}}chr}}-{{{{namespace[assoc]}}position}}-{{{{namespace[assoc]}}ref}}-{{{{namespace[assoc]}}alt}}"
                                }];
                                return l;
                            }()
                        ],
                    });
                    base.legend.origin.y = 15;
                    return base;
                }());
            }

        }}
    })
});

