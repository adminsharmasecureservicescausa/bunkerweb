#!/bin/sh

echo "Certbot started, domains = $DOMAINS"

first_domain="$(echo -n $DOMAINS | cut -d ',' -f 1 | sed 's/*\.//g')"
if [ "$EMAIL" = "" ] ; then
	EMAIL="contact@${first_domain}"
fi

if [ -f "/etc/letsencrypt/live/${first_domain}/fullchain.pem" ] ; then
	echo "Renewing certificates ..."
	certbot renew
else
	echo "Asking for certificates ..."
	certbot certonly -n --dns-google --dns-google-credentials /opt/google.json --email "$EMAIL" --agree-tos -d "$DOMAINS"
fi

echo "Fixing permissions ..."
chown -R 0:101 /etc/letsencrypt && chmod -R 770 /etc/letsencrypt

echo "Certbot ended, sleeping for 24 hours"

sleep 86400
