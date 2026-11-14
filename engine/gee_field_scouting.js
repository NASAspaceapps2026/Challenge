// Field Shift — T0.3 scouting script for GEE Code Editor
// https://code.earthengine.google.com
//
// Purpose: help pick 5-10 demo soybean fields in Sorriso / Lucas do Rio Verde (MT)
// that are (a) rainfed (no pivot), (b) >100ha, (c) soy every year, (d) clustered
// within ~20-30km so they share one climate point.
//
// How to use:
// 1. Paste this whole file into a new script in the GEE Code Editor.
// 2. Run it. Two map layers appear:
//    - "Dry season composite" (true color, Aug): pivots show up as bright green
//      circles against brown dormant land. Rule out anything circular.
//    - "NDVI peak season" (false color, Dec): helps see field boundaries and
//      confirm a crop was actually growing (soy canopy is vivid).
// 3. Use the Geometry drawing tool (toolbar above the map, polygon icon) to draw
//    a polygon over each candidate rectangular/irregular field. Rename each
//    geometry layer T1, T2, T3... (double-click the layer name in Geometry Imports).
// 4. Click anywhere inside a drawn or candidate field to print its NDVI time
//    series in the Console (confirms: bare Apr-Sep, rises Oct, peaks Dec-Jan,
//    drops Feb — the rainfed soybean signature; a pivot instead stays non-zero
//    through the dry months).
// 5. When happy with your T1..T10 polygons, run the EXPORT block at the bottom
//    (uncomment it) to print ready-to-copy GeoJSON coordinates to the Console,
//    or use Export.table.toDrive to get an actual .geojson file.

// ---- 1. Area of interest: Sorriso / Lucas do Rio Verde cluster ----
// Sorriso center approx -12.5447, -55.7217 ; Lucas do Rio Verde approx -13.0540, -55.9064
// A single point roughly between them keeps every field within ~25-30km.
var aoiCenter = ee.Geometry.Point([-55.80, -12.75]);
var aoi = aoiCenter.buffer(30000); // 30 km radius
Map.centerObject(aoi, 10);
Map.addLayer(aoi, {color: 'white'}, 'AOI (30km radius)', false);

// ---- 2. Cloud-masked Sentinel-2 SR helper ----
function maskS2(image) {
  var scl = image.select('SCL');
  // keep vegetation(4), bare soil(5), water(6), unclassified(7) — drop clouds/shadow/snow
  var mask = scl.eq(4).or(scl.eq(5)).or(scl.eq(6)).or(scl.eq(7));
  return image.updateMask(mask).divide(10000)
    .copyProperties(image, ['system:time_start']);
}

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(aoi)
  .map(maskS2);

// ---- 3. Dry-season composite (July-Aug, last 2 full dry seasons) ----
// This is the key "find the pivots" layer: anything green here, in the middle
// of the dry season, is almost certainly irrigated.
var dryComposite = s2
  .filterDate('2024-07-01', '2024-09-15')
  .median();

Map.addLayer(
  dryComposite,
  {bands: ['B4', 'B3', 'B2'], min: 0.02, max: 0.3},
  'Dry season composite (Aug) - look for green circles = pivots'
);

// ---- 4. Peak-growing-season composite (Dec) — field boundaries + canopy check ----
var peakComposite = s2
  .filterDate('2024-12-01', '2024-12-31')
  .median();

Map.addLayer(
  peakComposite,
  {bands: ['B8', 'B4', 'B3'], min: 0.02, max: 0.4},
  'Peak season false color (Dec) - vivid red = healthy canopy'
);

// ---- 5. NDVI time series on click (multi-year, confirms the rainfed signature) ----
function addNDVI(image) {
  var ndvi = image.normalizedDifference(['B8', 'B4']).rename('ndvi');
  return ndvi.copyProperties(image, ['system:time_start']);
}
var ndviCollection = s2.filterDate('2019-01-01', '2026-01-01').map(addNDVI);

Map.onClick(function (coords) {
  var point = ee.Geometry.Point([coords.lon, coords.lat]);
  print('Clicked:', coords.lon, coords.lat);

  var chart = ui.Chart.image.series({
    imageCollection: ndviCollection,
    region: point,
    reducer: ee.Reducer.mean(),
    scale: 10
  }).setOptions({
    title: 'NDVI time series at clicked point',
    vAxis: {title: 'NDVI', viewWindow: {min: 0, max: 1}},
    hAxis: {title: 'Date'},
    lineWidth: 1,
    pointSize: 2
  });
  print(chart);
  print('What to look for: bare/low (~0.2-0.3) Apr-Sep, sharp rise ~Oct, ' +
        'peak ~Dec-Jan (soy), drop ~Feb-Mar. If it stays >0.4 through Jun-Aug, ' +
        'suspect irrigation.');
});

print('Draw your candidate polygons with the Geometry tool, rename each layer ' +
      'T1, T2, ... in Geometry Imports, then click inside each one to check its ' +
      'NDVI history before finalizing.');

// ---- 6. AREA CHECK — run this once you've drawn your candidates ----
// Fields must be >100ha. List your drawn geometries below and run again;
// each area in hectares prints to the Console. Anything under 100 should be
// redrawn bigger (trace the real field edge, don't subdivide one field into
// several smaller shapes) or dropped.
var candidates = {T1: T1, T2: T2, T3: T3, T4: T4, T5: T5, T6: T6, T7: T7};
Object.keys(candidates).forEach(function (key) {
  var areaHa = ee.Geometry(candidates[key]).area().divide(10000);
  print(key + ' area (ha):', areaHa);
});

// ---- 6b. COMPARE ALL CANDIDATES' NDVI TOGETHER ----
// One chart, 7 colored lines — much faster than clicking each field.
var candidatesFc = ee.FeatureCollection(
  Object.keys(candidates).map(function (key) {
    return ee.Feature(ee.Geometry(candidates[key]), {id: key});
  })
);
var compareChart = ui.Chart.image.seriesByRegion({
  imageCollection: ndviCollection.filterDate('2022-01-01', '2026-01-01'),
  regions: candidatesFc,
  reducer: ee.Reducer.mean(),
  band: 'ndvi',
  scale: 10,
  seriesProperty: 'id'
}).setOptions({
  title: 'NDVI by field (2022-2025)',
  vAxis: {title: 'NDVI', viewWindow: {min: 0, max: 1}},
  hAxis: {title: 'Date'}
});
print(compareChart);
print('Read this as: lines that rise earlier = earlier planting; lines with a ' +
      'second bump after the main Feb-Mar drop = visible safrinha; a line that ' +
      'never drops near 0 in Jun-Sep = suspect irrigation, drop that field.');

// ---- 7. EXPORT — uncomment once your T1..T10 geometries are drawn ----
// Each drawn geometry becomes a variable named after its import (e.g. T1, T2...).
// List them here and run again to print GeoJSON-ready coordinates to the Console.
//
// var fields = ee.FeatureCollection([
//   ee.Feature(T1, {id: 'T1', name: 'Field 1 - early planting, no safrinha'}),
//   ee.Feature(T2, {id: 'T2', name: 'Field 2 - late planting, visible safrinha'})
//   // ... add the rest
// ]);
// print('Copy this geometry info or use Export.table.toDrive:', fields);
// Export.table.toDrive({
//   collection: fields,
//   description: 'fields_export',
//   fileFormat: 'GeoJSON'
// });
