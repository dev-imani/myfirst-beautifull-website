import { offer } from '../assets/images';
import Button from '../Components/Button';
import arrowRight from '../assets/icons/arrow-right.svg';

function SpecialOffer() {
  return (
    <div>
      <section className="flex justify-wrap items-center max-xl:flex-col-reverse gap-10 max-container">
        <div className="flex-1">
          <img
            src={offer}
            width={773}
            height={687}
            className="object-contain w-full"
          />
        </div>
        <div className="flex flex-1 flex-col">
          <h2 className="font-palanquin capitalize text-4xl font-bold lg:max-w-lg">
            <span className="text-coral-red inline-block mt-3">Special</span>
            <br />
            <span className="text-coral-red inline-block mt-3">Enjoyable</span>
            Offers
          </h2>
          <p className="mt-4 lg:max-w-lg info-text">
            Embark on a shopping journey with our special offers and discounts that redefine your shopping experience. From premium selection 
            to incredible savings, we have everything you need to make your shopping experience enjoyable.
          </p>
          <p className="mt-6 lg:max-w-lg info-text">
            Navigate through our collection and discover the perfect pair of shoes that suits your style and budget. Your journey with us is a great experience.
          </p>
          <div className="mt-11 flex gap-4">
            <Button label="Shop now" iconURL={arrowRight} />
            <Button label="Learn more" backgroundColor="bg-white" borderColor="border-slate-gray" textColor="text-slate-gray" />
          </div>
        </div>
      </section>
    </div>
  );
}

export default SpecialOffer;