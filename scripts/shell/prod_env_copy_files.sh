echo "Copying to Site Packages..."
cp -rf /tmp/integral_view/integral-view/common/python/fractalio/ /usr/lib/python2.6/site-packages/

echo "Copying salt modules"
cp -rf /tmp/integral_view/integral-view/monitoring/salt/_modules /srv/salt

echo "Copying monitoring utilities"
cp -rf /tmp/integral_view/integral-view/monitoring/python/ /opt/fractalio/monitoring/

echo "Updating Integral view -- Django app"
cp -rf /tmp/integral_view/integral-view/integral_view/ /opt/fractalio/integral_view/

