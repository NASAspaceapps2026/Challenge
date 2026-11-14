// Field Shift — TA.3: slope (SRTM) + area per field, for GEE Code Editor
// https://code.earthengine.google.com
//
// How to use:
// 1. Paste this whole file into a new script in the GEE Code Editor and Run.
// 2. The Console prints a CSV block: copy it into data/fields_attributes.csv
//    (columns per docs/CONTRACTS.md: field_id, slope_deg, area_ha).
//    (A Tasks export to Drive is also fired as a backup.)

// data/fields.geojson inlined — regenerate if data/fields.geojson changes:
var geojson = {"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[-55.54999812858917,-12.546552229529675],[-55.54716571586946,-12.557108423717525],[-55.53849681633332,-12.555181531691353],[-55.54167255180696,-12.54521172944736],[-55.54999812858917,-12.546552229529675]]]},"id":"0","properties":{"id":"T1","name":"Field 1"}},{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[-55.54107189046496,-12.545181272281917],[-55.53806781636829,-12.554648405787509],[-55.529313086143674,-12.552637716294173],[-55.53214549886341,-12.543421855124834],[-55.54107189046496,-12.545181272281917]]]},"id":"1","properties":{"id":"T2","name":"Field 2"}},{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[-55.531369961945664,-12.543593299964709],[-55.52879504129137,-12.552306480502889],[-55.51849535867418,-12.549876873276261],[-55.52072695657457,-12.54133117603442],[-55.531369961945664,-12.543593299964709]]]},"id":"2","properties":{"id":"T3","name":"Field 3"}},{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[-55.5422028568549,-12.544887344195649],[-55.544734862164944,-12.533241441467641],[-55.55125799448917,-12.534582003843369],[-55.55052843363712,-12.538310406280509],[-55.55134382517765,-12.541200928342843],[-55.55001344950626,-12.54606028362711],[-55.5422028568549,-12.544887344195649]]]},"id":"3","properties":{"id":"T4","name":"Field 4"}},{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[-55.54147578218733,-12.544098243741711],[-55.537098417075015,-12.543595552237813],[-55.53821421602522,-12.533709086620787],[-55.541819104941226,-12.526252094686667],[-55.546110639365054,-12.52734133167854],[-55.54147578218733,-12.544098243741711]]]},"id":"4","properties":{"id":"T5","name":"Field 5"}},{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[-55.525256239317855,-12.54078170127033],[-55.52512749328513,-12.529177506311573],[-55.534354292296364,-12.531188378964096],[-55.53452595367332,-12.542834374495177],[-55.525256239317855,-12.54078170127033]]]},"id":"5","properties":{"id":"T6","name":"Field 6"}},{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[-55.531018550002706,-12.554009877931216],[-55.52921610554469,-12.562890257244938],[-55.51844435414088,-12.56062830293936],[-55.521319682204854,-12.551873514521407],[-55.52612618002324,-12.553067407226617],[-55.531018550002706,-12.554009877931216]]]},"id":"6","properties":{"id":"T7","name":"Field 7"}}]};

var fields = ee.FeatureCollection(geojson.features.map(function (f) {
  return ee.Feature(ee.Geometry(f.geometry), f.properties);
}));

var slope = ee.Terrain.slope(ee.Image('USGS/SRTMGL1_003'));

var out = fields.map(function (f) {
  var meanSlope = slope.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: f.geometry(),
    scale: 30
  }).get('slope');
  return ee.Feature(null, {
    field_id: f.get('id'),
    slope_deg: ee.Number(meanSlope).format('%.2f'),
    area_ha: ee.Number(f.geometry().area({maxError: 1})).divide(10000).format('%.1f')
  });
});

// Print as a ready-to-paste CSV block
out.aggregate_array('field_id').evaluate(function (ids) {
  out.aggregate_array('slope_deg').evaluate(function (slopes) {
    out.aggregate_array('area_ha').evaluate(function (areas) {
      var lines = ['field_id,slope_deg,area_ha'];
      for (var i = 0; i < ids.length; i++) {
        lines.push(ids[i] + ',' + slopes[i] + ',' + areas[i]);
      }
      print('--- copy below into data/fields_attributes.csv ---');
      print(lines.join('\n'));
    });
  });
});

// Backup: export to Drive (run from the Tasks tab if the console print fails)
Export.table.toDrive({
  collection: out,
  description: 'fields_attributes',
  fileFormat: 'CSV',
  selectors: ['field_id', 'slope_deg', 'area_ha']
});
