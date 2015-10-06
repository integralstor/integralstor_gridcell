echo "Copying to Site Packages..."
cp -rf /tmp/integral_view/integral-view/common/python/fractalio/ /usr/lib/python2.6/site-packages/

echo "Copying salt modules"
cp -rf /tmp/integral_view/integral-view/salt/_modules /srv/salt/

echo "Copying scripts"
cp -rf /tmp/integral_view/integral-view/scripts/ /opt/integralstor/integralstor_gridcell/

echo "Copying scripts"
cp -rf /tmp/integral_view/integral-view/defaults/ /opt/integralstor/integralstor_gridcell/

echo "Updating Integral view -- Django app"
cp -rf /tmp/integral_view/integral-view/integral_view/ /opt/integralstor/integralstor_gridcell/integral_view/


