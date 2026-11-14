// Field Shift — TA.1: export NDVI series per field (Sentinel-2 + MODIS)
// https://code.earthengine.google.com
//
// FALLBACK ONLY — the team decided to run GEE exports through the Python
// API instead (see engine/gee_ndvi_export.py), so this doesn't need the
// Drive-export/manual-download dance. Keep this file only as a backup in
// case the Python/API setup breaks during the event — it needs nothing
// but a browser.
//
// Purpose: for each of the 7 demo fields in data/fields.geojson, build a
// 2019 -> today NDVI time series (Sentinel-2 10m where available, MODIS 250m
// to fill gaps/extend coverage) and export one CSV per field to Drive.
// Output matches docs/CONTRACTS.md: data/ndvi_<field_id>.csv, columns
// `date, ndvi_raw` (ndvi_smooth is added later by TB.1 — don't add it here).
//
// How to use:
// 1. Paste this whole file into a new script in the GEE Code Editor.
// 2. Run it. For each field T1..T7 a quick NDVI chart prints to the Console —
//    eyeball it for the rainfed soybean signature (bare Apr-Sep, rise Oct,
//    peak Dec-Jan, drop Feb) before firing exports; a broken chart (empty,
//    all-null) means the geometry or date filter is wrong for that field.
// 3. Open the Tasks tab (right panel). Seven tasks named "ndvi_export_T1"
//    ... "ndvi_export_T7" are queued. Click RUN on each (GEE doesn't let a
//    script auto-start exports) — do this in the first hour, they can take
//    a while since Sentinel-2 is a lot of images over 7+ years.
// 4. When a task finishes, download the CSV from Drive (folder
//    "FieldShift_NDVI") and save it as data/ndvi_<field_id>.csv in the repo
//    (e.g. ndvi_T1.csv). Columns are already exactly `date, ndvi_raw`.

// ---- 1. Fields — embedded straight from data/fields.geojson (T0.3 output) ----
// Keeping the coordinates inline (instead of redrawing geometries in the
// Code Editor) means this script is reproducible from the repo alone.
var fieldsGeoJson = {
  "type": "FeatureCollection",
  "features": [
    {"type": "Feature", "properties": {"id": "T1", "name": "Field 1"}, "geometry": {"type": "Polygon", "coordinates": [[[-55.54999812858917,-12.546552229529675],[-55.54716571586946,-12.557108423717525],[-55.53849681633332,-12.555181531691353],[-55.54167255180696,-12.54521172944736],[-55.54999812858917,-12.546552229529675]]]}},
    {"type": "Feature", "properties": {"id": "T2", "name": "Field 2"}, "geometry": {"type": "Polygon", "coordinates": [[[-55.54107189046496,-12.545181272281917],[-55.53806781636829,-12.554648405787509],[-55.529313086143674,-12.552637716294173],[-55.53214549886341,-12.543421855124834],[-55.54107189046496,-12.545181272281917]]]}},
    {"type": "Feature", "properties": {"id": "T3", "name": "Field 3"}, "geometry": {"type": "Polygon", "coordinates": [[[-55.531369961945664,-12.543593299964709],[-55.52879504129137,-12.552306480502889],[-55.51849535867418,-12.549876873276261],[-55.52072695657457,-12.54133117603442],[-55.531369961945664,-12.543593299964709]]]}},
    {"type": "Feature", "properties": {"id": "T4", "name": "Field 4"}, "geometry": {"type": "Polygon", "coordinates": [[[-55.5422028568549,-12.544887344195649],[-55.544734862164944,-12.533241441467641],[-55.55125799448917,-12.534582003843369],[-55.55052843363712,-12.538310406280509],[-55.55134382517765,-12.541200928342843],[-55.55001344950626,-12.54606028362711],[-55.5422028568549,-12.544887344195649]]]}},
    {"type": "Feature", "properties": {"id": "T5", "name": "Field 5"}, "geometry": {"type": "Polygon", "coordinates": [[[-55.54147578218733,-12.544098243741711],[-55.537098417075015,-12.543595552237813],[-55.53821421602522,-12.533709086620787],[-55.541819104941226,-12.526252094686667],[-55.546110639365054,-12.52734133167854],[-55.54147578218733,-12.544098243741711]]]}},
    {"type": "Feature", "properties": {"id": "T6", "name": "Field 6"}, "geometry": {"type": "Polygon", "coordinates": [[[-55.525256239317855,-12.54078170127033],[-55.52512749328513,-12.529177506311573],[-55.534354292296364,-12.531188378964096],[-55.53452595367332,-12.542834374495177],[-55.525256239317855,-12.54078170127033]]]}},
    {"type": "Feature", "properties": {"id": "T7", "name": "Field 7"}, "geometry": {"type": "Polygon", "coordinates": [[[-55.531018550002706,-12.554009877931216],[-55.52921610554469,-12.562890257244938],[-55.51844435414088,-12.56062830293936],[-55.521319682204854,-12.551873514521407],[-55.52612618002324,-12.553067407226617],[-55.531018550002706,-12.554009877931216]]]}}
  ]
};
var fields = ee.FeatureCollection(fieldsGeoJson);

// ---- 2. Date range: 2019-01-01 -> today ----
var START_DATE = '2019-01-01';
var END_DATE = new Date().toISOString().slice(0, 10); // plain client-side JS, no server round-trip

// ---- 3. Sentinel-2 SR: cloud-masked NDVI, per-field spatial mean, 10m ----
function maskS2(image) {
  var scl = image.select('SCL');
  // keep vegetation(4), bare soil(5), water(6), unclassified(7) — drop clouds/shadow/snow
  var mask = scl.eq(4).or(scl.eq(5)).or(scl.eq(6)).or(scl.eq(7));
  return image.updateMask(mask).divide(10000)
    .copyProperties(image, ['system:time_start']);
}

function s2NdviSeries(geom) {
  var col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(geom)
    .filterDate(START_DATE, END_DATE)
    .map(maskS2)
    .map(function (img) {
      var ndvi = img.normalizedDifference(['B8', 'B4']).rename('ndvi');
      return ndvi.copyProperties(img, ['system:time_start']);
    });

  return col.map(function (img) {
    var stat = img.reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: geom,
      scale: 10,
      maxPixels: 1e9
    });
    return ee.Feature(null, {
      date: img.date().format('YYYY-MM-dd'),
      ndvi_raw: stat.get('ndvi')
    });
  }).filter(ee.Filter.notNull(['ndvi_raw']));
}

// ---- 4. MODIS MOD13Q1: 16-day 250m NDVI, QA-filtered, fills S2 gaps ----
function modisNdviSeries(geom) {
  var col = ee.ImageCollection('MODIS/061/MOD13Q1')
    .filterBounds(geom)
    .filterDate(START_DATE, END_DATE)
    .map(function (img) {
      var good = img.select('SummaryQA').lte(1); // 0 good, 1 marginal; drop snow/cloud
      var ndvi = img.select('NDVI').multiply(0.0001).updateMask(good).rename('ndvi');
      return ndvi.copyProperties(img, ['system:time_start']);
    });

  return col.map(function (img) {
    var stat = img.reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: geom,
      scale: 250,
      maxPixels: 1e9
    });
    return ee.Feature(null, {
      date: img.date().format('YYYY-MM-dd'),
      ndvi_raw: stat.get('ndvi')
    });
  }).filter(ee.Filter.notNull(['ndvi_raw']));
}

// ---- 5. Build + chart + export, one field at a time ----
var fieldIds = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];

fieldIds.forEach(function (fieldId) {
  var geom = fields.filter(ee.Filter.eq('id', fieldId)).first().geometry();

  var merged = s2NdviSeries(geom)
    .merge(modisNdviSeries(geom))
    .sort('date');

  // quick sanity chart — eyeball the soybean wave before firing the export
  var chart = ui.Chart.feature.byFeature(merged, 'date', ['ndvi_raw'])
    .setChartType('ScatterChart')
    .setOptions({
      title: fieldId + ' — NDVI raw (Sentinel-2 + MODIS)',
      vAxis: {title: 'NDVI', viewWindow: {min: 0, max: 1}},
      hAxis: {title: 'date'},
      pointSize: 2
    });
  print(chart);

  Export.table.toDrive({
    collection: merged,
    description: 'ndvi_export_' + fieldId,
    folder: 'FieldShift_NDVI',
    fileNamePrefix: 'ndvi_' + fieldId,
    fileFormat: 'CSV',
    selectors: ['date', 'ndvi_raw']
  });
});

print('7 export tasks queued (ndvi_export_T1 .. ndvi_export_T7). Open the ' +
      'Tasks tab and click RUN on each — they are not started automatically.');
