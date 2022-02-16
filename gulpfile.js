var gulp = require('gulp');
var concat = require('gulp-concat');

gulp.task('default', function () {
});

gulp.task('vendor-js', function () {
    return gulp.src([
        'node_modules/bootstrap/dist/js/bootstrap.bundle.min.js',
        'node_modules/@mux/upchunk/dist/upchunk.js',
        'node_modules/video.js/dist/video.min.js',
        'node_modules/@streamroot/videojs-hlsjs-plugin/videojs-hlsjs-plugin.js',
        'node_modules/videojs-hotkeys/videojs.hotkeys.min.js'
    ]).pipe(
        concat('all.js')
    ).pipe(gulp.dest('./muxltiproducer/static/muxltiproducer/vendor'));
});
gulp.task('vendor-css', function () {
    return gulp.src([
        'node_modules/bootstrap/dist/css/bootstrap.min.css',
        'node_modules/video.js/dist/video-js.min.css',
        'node_modules/@videojs/themes/dist/city/index.css',
        'node_modules/bootstrap-icons/font/bootstrap-icons.css'
    ]).pipe(
        concat('all.css')
    ).pipe(gulp.dest('./muxltiproducer/static/muxltiproducer/vendor'));
});
gulp.task('vendor-fonts', function () {
    return gulp.src([
        'node_modules/bootstrap-icons/font/fonts/bootstrap-icons.woff',
        'node_modules/bootstrap-icons/font/fonts/bootstrap-icons.woff2',
    ])
        .pipe(gulp.dest('./muxltiproducer/static/muxltiproducer/vendor/fonts'));
});
gulp.task('vendor-map', function () {
    return gulp.src([
        './node_modules/bootstrap/dist/css/bootstrap.min.css.map',
        './node_modules/@mux/upchunk/dist/upchunk.js.map'
    ])
        .pipe(gulp.dest('./muxltiproducer/static/muxltiproducer/vendor'));
});

gulp.task('vendor', gulp.series('vendor-js', 'vendor-css', 'vendor-fonts', 'vendor-map'));
gulp.task('default', gulp.series('vendor'));
