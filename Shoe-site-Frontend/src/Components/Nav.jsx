import { hamburger } from '../assets/icons';
import { headerLogo } from '../assets/images';
import { navLinks } from '../Constants';

function Nav() {
  return (
    <div>
      <header className='padding-x py-8 absolute z-10 w-full'>
        <nav className='flex justify-between items-center max-content '>
          <a href="/">
            <img src={headerLogo}
             alt="Logo"
             width={130}
             height={29} />
          </a>
          <ul className="flex-1 flex justify-center items-center gap-16 max-lg:hidden">
            {navLinks.map((itemk) => (
              <li key={itemk.label}>
                <a href={itemk.href}
                className='font-montserrat leading-normal text-lg text-slate-gray'>
                  {itemk.label}
                </a>
              </li>
            ))}
          </ul>
          <div className=' hidden max-lg:block'>
            <img src={hamburger} alt="hamburger" width={25} height={25} />
          </div>
        </nav>
      </header>
    </div>
  );
}

export default Nav;
