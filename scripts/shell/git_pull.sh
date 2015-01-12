echo "Copying to Site Packages..."
cp -rf /usr/lib/python2.6/site-packages/ /tmp/integral_view/integral-view/common/python/fractalio/ 

echo "Copying salt modules"
cp -rf /srv/salt /tmp/integral_view/integral-view/monitoring/salt/_modules 

echo "Copying monitoring utilities"
cp -rf /opt/fractalio/monitoring/ /tmp/integral_view/integral-view/monitoring/python/

echo "Updating Integral view -- Django app"
cp -rf /opt/fractalio/integral_view/ /tmp/integral_view/integral-view/integral_view/


