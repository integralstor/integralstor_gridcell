echo "Copying to Site Packages..."
cp -rf /tmp/integral_view/integral-view/common/python/fractalio/ /usr/lib/python2.6/site-packages/

echo "Copying salt modules"
cp -rf /tmp/integral_view/integral-view/salt/_modules /srv/salt

echo "Copying scripts"
cp -rf /tmp/integral_view/integral-view/scripts/ /opt/fractalio/


echo "Updating Integral view -- Django app"
cp -rf /tmp/integral_view/integral-view/integral_view/ /opt/fractalio/integral_view/


