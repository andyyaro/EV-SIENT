// The EV-SIENT Bolt Pin from the logo kit (brand/evsient-mark.svg): a map pin whose point kicks
// sideways into a bolt. It fills with currentColor so it follows the theme like the icons do.

export function BrandMark({ size }: { size: number }) {
  return (
    <svg className="hig-icon" viewBox="0 0 64 64" width={size} height={size} aria-hidden="true" focusable="false">
      <path
        fillRule="evenodd"
        fill="currentColor"
        d="M27.283 58.704L24.592 40.17A1.813 1.813 0 0 0 23.33 38.698A17.118 17.118 0 1 1 43.619 30.079A0.906 0.906 0 0 0 44.427 31.396L52.383 31.396A1.208 1.208 0 0 1 53.294 33.398L30.443 59.634A1.813 1.813 0 0 1 27.283 58.704ZM28.353 15.889A6.444 6.444 0 1 0 28.353 28.778A6.444 6.444 0 1 0 28.353 15.889Z"
      />
    </svg>
  );
}
