import React from 'react';
import PropTypes from 'prop-types';
import { usePaymentIframe } from '../../hooks';

const PaymentIframe = ({
  paymentIframeUrl, paymentIframeHeight, paymentIframeOnLoaded, className,
}) => {
  const style = {
    height: `${paymentIframeHeight}px`,
  };

  return (
    <iframe
      title="payments"
      data-bold-pigi-iframe
      className={className}
      src={paymentIframeUrl}
      style={style}
      onLoad={paymentIframeOnLoaded}
    />
  );
};

PaymentIframe.propTypes = {
  paymentIframeUrl: PropTypes.string,
  paymentIframeHeight: PropTypes.number,
  paymentIframeOnLoaded: PropTypes.func,
  className: PropTypes.string,
};

const MemoizedPaymentIframe = React.memo(PaymentIframe);

const PaymentIframeContainer = ({ className }) => {
  const { data, paymentIframeOnLoaded } = usePaymentIframe();

  return (
    <MemoizedPaymentIframe
      paymentIframeUrl={data.url}
      paymentIframeHeight={data.height}
      paymentIframeOnLoaded={paymentIframeOnLoaded}
      className={className}
    />
  );
};

PaymentIframeContainer.propTypes = {
  className: PropTypes.string,
};

export default PaymentIframeContainer;
